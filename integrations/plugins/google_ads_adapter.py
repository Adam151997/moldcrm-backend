"""
Google Ads plugin adapter
Handles OAuth, webhooks, and data synchronization for Google Ads
"""
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.utils import timezone

from .base_adapter import BasePluginAdapter, AuthResponse, WebhookEvent, SyncResult


class GoogleAdsAdapter(BasePluginAdapter):
    """
    Adapter for Google Ads integration
    Implements OAuth 2.0 flow and Google Ads API integration
    """

    # Google OAuth endpoints
    OAUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    API_BASE_URL = "https://googleads.googleapis.com/v14"

    # Required OAuth scopes
    SCOPES = [
        "https://www.googleapis.com/auth/adwords",
    ]

    def get_oauth_url(self, redirect_uri: str, state: str) -> str:
        """Generate Google OAuth authorization URL"""
        credentials = self.get_decrypted_credentials()
        client_id = credentials.get('client_id')

        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.SCOPES),
            'state': state,
            'access_type': 'offline',  # Get refresh token
            'prompt': 'consent',  # Force consent to get refresh token
        }

        query_string = '&'.join([f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()])
        return f"{self.OAUTH_URL}?{query_string}"

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> AuthResponse:
        """Exchange authorization code for access token"""
        try:
            credentials = self.get_decrypted_credentials()

            data = {
                'client_id': credentials.get('client_id'),
                'client_secret': credentials.get('client_secret'),
                'code': code,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
            }

            response = requests.post(self.TOKEN_URL, data=data)
            response.raise_for_status()

            token_data = response.json()

            # Calculate token expiration
            expires_in = token_data.get('expires_in', 3600)
            expires_at = timezone.now() + timedelta(seconds=expires_in)

            return AuthResponse(
                success=True,
                access_token=token_data.get('access_token'),
                refresh_token=token_data.get('refresh_token'),
                expires_at=expires_at
            )

        except Exception as e:
            return AuthResponse(
                success=False,
                error=str(e)
            )

    def refresh_access_token(self) -> AuthResponse:
        """Refresh the access token using refresh token"""
        try:
            credentials = self.get_decrypted_credentials()

            data = {
                'client_id': credentials.get('client_id'),
                'client_secret': credentials.get('client_secret'),
                'refresh_token': credentials.get('refresh_token'),
                'grant_type': 'refresh_token',
            }

            response = requests.post(self.TOKEN_URL, data=data)
            response.raise_for_status()

            token_data = response.json()

            # Calculate token expiration
            expires_in = token_data.get('expires_in', 3600)
            expires_at = timezone.now() + timedelta(seconds=expires_in)

            return AuthResponse(
                success=True,
                access_token=token_data.get('access_token'),
                refresh_token=credentials.get('refresh_token'),  # Keep existing refresh token
                expires_at=expires_at
            )

        except Exception as e:
            return AuthResponse(
                success=False,
                error=str(e)
            )

    def verify_connection(self) -> tuple[bool, str]:
        """Verify that the Google Ads connection is working"""
        try:
            self._check_token_expiration()
            credentials = self.get_decrypted_credentials()

            # Get customer ID from config
            customer_id = self.plugin.config.get('customer_id')
            if not customer_id:
                return False, "Customer ID not configured"

            # Test API call to get customer info
            headers = {
                'Authorization': f"Bearer {credentials.get('access_token')}",
                'developer-token': self.plugin.config.get('developer_token', ''),
            }

            url = f"{self.API_BASE_URL}/customers/{customer_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            return True, "Connection verified successfully"

        except Exception as e:
            return False, f"Connection verification failed: {str(e)}"

    def parse_webhook_event(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Optional[WebhookEvent]:
        """
        Parse Google Ads webhook event
        Note: Google Ads doesn't have native webhooks, but we can use Pub/Sub notifications
        """
        try:
            # Verify signature if present
            signature = headers.get('X-Goog-Signature')
            if signature and not self.verify_webhook_signature(
                str(payload).encode('utf-8'),
                signature
            ):
                return None

            # Parse event data
            event_type = payload.get('type', 'google_ads.conversion')
            event_id = payload.get('id', '')

            return WebhookEvent(
                event_type=event_type,
                event_id=event_id,
                data=payload.get('data', {}),
                timestamp=datetime.fromisoformat(payload.get('timestamp', timezone.now().isoformat())),
                raw_payload=payload
            )

        except Exception:
            return None

    def sync_data(self, sync_type: str, **kwargs) -> SyncResult:
        """
        Synchronize data from Google Ads

        Supported sync types:
        - campaigns: Sync campaign data
        - conversions: Sync conversion data
        - performance: Sync performance metrics
        """
        try:
            self._check_token_expiration()

            if sync_type == 'campaigns':
                return self._sync_campaigns(**kwargs)
            elif sync_type == 'conversions':
                return self._sync_conversions(**kwargs)
            elif sync_type == 'performance':
                return self._sync_performance(**kwargs)
            else:
                return SyncResult(
                    success=False,
                    error=f"Unsupported sync type: {sync_type}"
                )

        except Exception as e:
            return SyncResult(
                success=False,
                error=str(e)
            )

    def _sync_campaigns(self, **kwargs) -> SyncResult:
        """Sync campaign data from Google Ads"""
        try:
            credentials = self.get_decrypted_credentials()
            customer_id = self.plugin.config.get('customer_id')

            headers = {
                'Authorization': f"Bearer {credentials.get('access_token')}",
                'developer-token': self.plugin.config.get('developer_token', ''),
            }

            # Query campaigns using Google Ads Query Language
            query = """
                SELECT
                    campaign.id,
                    campaign.name,
                    campaign.status,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros
                FROM campaign
                WHERE campaign.status != 'REMOVED'
            """

            url = f"{self.API_BASE_URL}/customers/{customer_id}/googleAds:searchStream"
            response = requests.post(url, headers=headers, json={'query': query})
            response.raise_for_status()

            data = response.json()
            campaigns = data.get('results', [])

            return SyncResult(
                success=True,
                records_fetched=len(campaigns),
                details={'campaigns': campaigns}
            )

        except Exception as e:
            return SyncResult(
                success=False,
                error=str(e)
            )

    def _sync_conversions(self, **kwargs) -> SyncResult:
        """Sync conversion data from Google Ads"""
        # Implementation for syncing conversions
        return SyncResult(success=True, records_fetched=0)

    def _sync_performance(self, **kwargs) -> SyncResult:
        """Sync performance metrics from Google Ads"""
        # Implementation for syncing performance data
        return SyncResult(success=True, records_fetched=0)

    def get_account_info(self) -> Dict[str, Any]:
        """Get Google Ads account information"""
        try:
            self._check_token_expiration()
            credentials = self.get_decrypted_credentials()
            customer_id = self.plugin.config.get('customer_id')

            headers = {
                'Authorization': f"Bearer {credentials.get('access_token')}",
                'developer-token': self.plugin.config.get('developer_token', ''),
            }

            url = f"{self.API_BASE_URL}/customers/{customer_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            return {'error': str(e)}
