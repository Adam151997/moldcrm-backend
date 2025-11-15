"""
Meta Ads (Facebook & Instagram) plugin adapter
Handles OAuth, webhooks, and data synchronization for Meta advertising platforms
"""
import requests
import hmac
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.utils import timezone

from .base_adapter import BasePluginAdapter, AuthResponse, WebhookEvent, SyncResult


class MetaAdsAdapter(BasePluginAdapter):
    """
    Adapter for Meta Ads (Facebook & Instagram) integration
    Implements OAuth 2.0 flow and Meta Marketing API integration
    """

    # Meta OAuth endpoints
    OAUTH_URL = "https://www.facebook.com/v18.0/dialog/oauth"
    TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"
    API_BASE_URL = "https://graph.facebook.com/v18.0"

    # Required permissions
    SCOPES = [
        "ads_management",
        "ads_read",
        "business_management",
        "leads_retrieval",  # For lead ads
    ]

    def get_oauth_url(self, redirect_uri: str, state: str) -> str:
        """Generate Meta OAuth authorization URL"""
        credentials = self.get_decrypted_credentials()
        client_id = credentials.get('client_id')

        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'state': state,
            'scope': ','.join(self.SCOPES),
            'response_type': 'code',
        }

        query_string = '&'.join([f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()])
        return f"{self.OAUTH_URL}?{query_string}"

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> AuthResponse:
        """Exchange authorization code for access token"""
        try:
            credentials = self.get_decrypted_credentials()

            params = {
                'client_id': credentials.get('client_id'),
                'client_secret': credentials.get('client_secret'),
                'code': code,
                'redirect_uri': redirect_uri,
            }

            response = requests.get(self.TOKEN_URL, params=params)
            response.raise_for_status()

            token_data = response.json()

            # Get long-lived token
            long_lived_token = self._exchange_for_long_lived_token(token_data.get('access_token'))

            # Meta tokens typically last 60 days
            expires_at = timezone.now() + timedelta(days=60)

            return AuthResponse(
                success=True,
                access_token=long_lived_token,
                refresh_token=None,  # Meta doesn't use refresh tokens in the same way
                expires_at=expires_at
            )

        except Exception as e:
            return AuthResponse(
                success=False,
                error=str(e)
            )

    def _exchange_for_long_lived_token(self, short_lived_token: str) -> str:
        """Exchange short-lived token for long-lived token"""
        try:
            credentials = self.get_decrypted_credentials()

            params = {
                'grant_type': 'fb_exchange_token',
                'client_id': credentials.get('client_id'),
                'client_secret': credentials.get('client_secret'),
                'fb_exchange_token': short_lived_token,
            }

            response = requests.get(self.TOKEN_URL, params=params)
            response.raise_for_status()

            token_data = response.json()
            return token_data.get('access_token')

        except Exception:
            return short_lived_token  # Return short-lived if exchange fails

    def refresh_access_token(self) -> AuthResponse:
        """
        Refresh the access token
        Note: Meta uses long-lived tokens (60 days) instead of refresh tokens
        """
        try:
            # Meta doesn't have traditional refresh tokens
            # We need to re-exchange the current token for a new long-lived token
            credentials = self.get_decrypted_credentials()
            current_token = credentials.get('access_token')

            new_token = self._exchange_for_long_lived_token(current_token)
            expires_at = timezone.now() + timedelta(days=60)

            return AuthResponse(
                success=True,
                access_token=new_token,
                refresh_token=None,
                expires_at=expires_at
            )

        except Exception as e:
            return AuthResponse(
                success=False,
                error=str(e)
            )

    def verify_connection(self) -> tuple[bool, str]:
        """Verify that the Meta Ads connection is working"""
        try:
            self._check_token_expiration()
            credentials = self.get_decrypted_credentials()

            # Get ad account ID from config
            ad_account_id = self.plugin.config.get('ad_account_id')
            if not ad_account_id:
                return False, "Ad Account ID not configured"

            # Test API call to get ad account info
            params = {
                'access_token': credentials.get('access_token'),
                'fields': 'name,account_status,currency'
            }

            url = f"{self.API_BASE_URL}/act_{ad_account_id}"
            response = requests.get(url, params=params)
            response.raise_for_status()

            account_data = response.json()
            account_name = account_data.get('name', 'Unknown')

            return True, f"Connected to {account_name}"

        except Exception as e:
            return False, f"Connection verification failed: {str(e)}"

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Meta webhook signature"""
        if not self.plugin.webhook_secret:
            return False

        # Meta uses sha256 with app secret
        expected_signature = 'sha256=' + hmac.new(
            self.plugin.webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    def parse_webhook_event(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Optional[WebhookEvent]:
        """
        Parse Meta Ads webhook event
        Meta sends webhooks for lead ads and other events
        """
        try:
            # Handle verification challenge
            if 'hub.challenge' in payload:
                return None  # This is handled separately in the webhook view

            # Verify signature
            signature = headers.get('X-Hub-Signature-256', '')
            if signature and not self.verify_webhook_signature(
                str(payload).encode('utf-8'),
                signature
            ):
                return None

            # Parse event data
            entry = payload.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]

            field = changes.get('field', '')
            value = changes.get('value', {})

            # Determine event type
            event_type = f"meta_ads.{field}"
            event_id = value.get('id', entry.get('id', ''))

            return WebhookEvent(
                event_type=event_type,
                event_id=event_id,
                data=value,
                timestamp=datetime.fromtimestamp(entry.get('time', timezone.now().timestamp())),
                raw_payload=payload
            )

        except Exception:
            return None

    def sync_data(self, sync_type: str, **kwargs) -> SyncResult:
        """
        Synchronize data from Meta Ads

        Supported sync types:
        - campaigns: Sync campaign data
        - leads: Sync lead ads data
        - insights: Sync performance insights
        """
        try:
            self._check_token_expiration()

            if sync_type == 'campaigns':
                return self._sync_campaigns(**kwargs)
            elif sync_type == 'leads':
                return self._sync_leads(**kwargs)
            elif sync_type == 'insights':
                return self._sync_insights(**kwargs)
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
        """Sync campaign data from Meta Ads"""
        try:
            credentials = self.get_decrypted_credentials()
            ad_account_id = self.plugin.config.get('ad_account_id')

            params = {
                'access_token': credentials.get('access_token'),
                'fields': 'id,name,status,objective,effective_status',
            }

            url = f"{self.API_BASE_URL}/act_{ad_account_id}/campaigns"
            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            campaigns = data.get('data', [])

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

    def _sync_leads(self, **kwargs) -> SyncResult:
        """Sync lead ads data from Meta"""
        try:
            credentials = self.get_decrypted_credentials()
            ad_account_id = self.plugin.config.get('ad_account_id')

            # Get lead gen forms
            params = {
                'access_token': credentials.get('access_token'),
                'fields': 'leads{id,created_time,field_data}',
            }

            url = f"{self.API_BASE_URL}/act_{ad_account_id}/leadgen_forms"
            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            forms = data.get('data', [])

            # Collect all leads from all forms
            all_leads = []
            for form in forms:
                leads = form.get('leads', {}).get('data', [])
                all_leads.extend(leads)

            return SyncResult(
                success=True,
                records_fetched=len(all_leads),
                details={'leads': all_leads}
            )

        except Exception as e:
            return SyncResult(
                success=False,
                error=str(e)
            )

    def _sync_insights(self, **kwargs) -> SyncResult:
        """Sync performance insights from Meta Ads"""
        try:
            credentials = self.get_decrypted_credentials()
            ad_account_id = self.plugin.config.get('ad_account_id')

            params = {
                'access_token': credentials.get('access_token'),
                'fields': 'impressions,clicks,spend,conversions',
                'level': 'campaign',
                'time_range': {'since': kwargs.get('since', '7d'), 'until': kwargs.get('until', 'today')}
            }

            url = f"{self.API_BASE_URL}/act_{ad_account_id}/insights"
            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            insights = data.get('data', [])

            return SyncResult(
                success=True,
                records_fetched=len(insights),
                details={'insights': insights}
            )

        except Exception as e:
            return SyncResult(
                success=False,
                error=str(e)
            )

    def get_account_info(self) -> Dict[str, Any]:
        """Get Meta Ads account information"""
        try:
            self._check_token_expiration()
            credentials = self.get_decrypted_credentials()
            ad_account_id = self.plugin.config.get('ad_account_id')

            params = {
                'access_token': credentials.get('access_token'),
                'fields': 'name,account_status,currency,timezone_name,spend_cap'
            }

            url = f"{self.API_BASE_URL}/act_{ad_account_id}"
            response = requests.get(url, params=params)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            return {'error': str(e)}
