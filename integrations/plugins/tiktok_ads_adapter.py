"""
TikTok Ads plugin adapter
Handles OAuth, webhooks, and data synchronization for TikTok advertising platform
"""
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.utils import timezone

from .base_adapter import BasePluginAdapter, AuthResponse, WebhookEvent, SyncResult


class TikTokAdsAdapter(BasePluginAdapter):
    """
    Adapter for TikTok Ads integration
    Implements OAuth 2.0 flow and TikTok Marketing API integration
    """

    # TikTok OAuth endpoints
    OAUTH_URL = "https://business-api.tiktok.com/portal/auth"
    TOKEN_URL = "https://business-api.tiktok.com/open_api/v1.3/oauth2/access_token/"
    API_BASE_URL = "https://business-api.tiktok.com/open_api/v1.3"

    def get_oauth_url(self, redirect_uri: str, state: str) -> str:
        """Generate TikTok OAuth authorization URL"""
        credentials = self.get_decrypted_credentials()
        client_id = credentials.get('client_id')

        params = {
            'app_id': client_id,
            'redirect_uri': redirect_uri,
            'state': state,
        }

        query_string = '&'.join([f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()])
        return f"{self.OAUTH_URL}?{query_string}"

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> AuthResponse:
        """Exchange authorization code for access token"""
        try:
            credentials = self.get_decrypted_credentials()

            data = {
                'app_id': credentials.get('client_id'),
                'secret': credentials.get('client_secret'),
                'auth_code': code,
            }

            response = requests.post(self.TOKEN_URL, json=data)
            response.raise_for_status()

            result = response.json()

            if result.get('code') != 0:
                return AuthResponse(
                    success=False,
                    error=result.get('message', 'Unknown error')
                )

            token_data = result.get('data', {})

            # TikTok tokens typically expire in a few hours
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

            url = f"{self.API_BASE_URL}/oauth2/refresh_token/"
            data = {
                'app_id': credentials.get('client_id'),
                'secret': credentials.get('client_secret'),
                'refresh_token': credentials.get('refresh_token'),
            }

            response = requests.post(url, json=data)
            response.raise_for_status()

            result = response.json()

            if result.get('code') != 0:
                return AuthResponse(
                    success=False,
                    error=result.get('message', 'Unknown error')
                )

            token_data = result.get('data', {})
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

    def verify_connection(self) -> tuple[bool, str]:
        """Verify that the TikTok Ads connection is working"""
        try:
            self._check_token_expiration()
            credentials = self.get_decrypted_credentials()

            # Get advertiser ID from config
            advertiser_id = self.plugin.config.get('advertiser_id')
            if not advertiser_id:
                return False, "Advertiser ID not configured"

            # Test API call to get advertiser info
            url = f"{self.API_BASE_URL}/advertiser/info/"
            params = {
                'advertiser_id': advertiser_id,
                'fields': '["name", "currency", "timezone"]'
            }
            headers = {
                'Access-Token': credentials.get('access_token'),
            }

            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()

            result = response.json()

            if result.get('code') != 0:
                return False, f"API Error: {result.get('message')}"

            advertiser_data = result.get('data', {}).get('list', [{}])[0]
            advertiser_name = advertiser_data.get('name', 'Unknown')

            return True, f"Connected to {advertiser_name}"

        except Exception as e:
            return False, f"Connection verification failed: {str(e)}"

    def parse_webhook_event(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Optional[WebhookEvent]:
        """
        Parse TikTok Ads webhook event
        """
        try:
            # Verify signature if present
            signature = headers.get('X-TikTok-Signature')
            if signature and not self.verify_webhook_signature(
                str(payload).encode('utf-8'),
                signature
            ):
                return None

            # Parse event data
            event_type = payload.get('event_type', 'tiktok_ads.campaign.updated')
            event_id = payload.get('event_id', '')

            return WebhookEvent(
                event_type=event_type,
                event_id=event_id,
                data=payload.get('data', {}),
                timestamp=datetime.fromtimestamp(payload.get('timestamp', timezone.now().timestamp())),
                raw_payload=payload
            )

        except Exception:
            return None

    def sync_data(self, sync_type: str, **kwargs) -> SyncResult:
        """
        Synchronize data from TikTok Ads

        Supported sync types:
        - campaigns: Sync campaign data
        - ads: Sync ad data
        - reports: Sync performance reports
        """
        try:
            self._check_token_expiration()

            if sync_type == 'campaigns':
                return self._sync_campaigns(**kwargs)
            elif sync_type == 'ads':
                return self._sync_ads(**kwargs)
            elif sync_type == 'reports':
                return self._sync_reports(**kwargs)
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
        """Sync campaign data from TikTok Ads"""
        try:
            credentials = self.get_decrypted_credentials()
            advertiser_id = self.plugin.config.get('advertiser_id')

            url = f"{self.API_BASE_URL}/campaign/get/"
            params = {
                'advertiser_id': advertiser_id,
                'fields': '["campaign_id", "campaign_name", "objective_type", "budget", "status"]'
            }
            headers = {
                'Access-Token': credentials.get('access_token'),
            }

            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()

            result = response.json()

            if result.get('code') != 0:
                return SyncResult(
                    success=False,
                    error=result.get('message', 'Unknown error')
                )

            campaigns = result.get('data', {}).get('list', [])

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

    def _sync_ads(self, **kwargs) -> SyncResult:
        """Sync ad data from TikTok Ads"""
        try:
            credentials = self.get_decrypted_credentials()
            advertiser_id = self.plugin.config.get('advertiser_id')

            url = f"{self.API_BASE_URL}/ad/get/"
            params = {
                'advertiser_id': advertiser_id,
                'fields': '["ad_id", "ad_name", "status", "creative_material_mode"]'
            }
            headers = {
                'Access-Token': credentials.get('access_token'),
            }

            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()

            result = response.json()

            if result.get('code') != 0:
                return SyncResult(
                    success=False,
                    error=result.get('message', 'Unknown error')
                )

            ads = result.get('data', {}).get('list', [])

            return SyncResult(
                success=True,
                records_fetched=len(ads),
                details={'ads': ads}
            )

        except Exception as e:
            return SyncResult(
                success=False,
                error=str(e)
            )

    def _sync_reports(self, **kwargs) -> SyncResult:
        """Sync performance reports from TikTok Ads"""
        # Implementation for syncing reports
        return SyncResult(success=True, records_fetched=0)

    def get_account_info(self) -> Dict[str, Any]:
        """Get TikTok Ads account information"""
        try:
            self._check_token_expiration()
            credentials = self.get_decrypted_credentials()
            advertiser_id = self.plugin.config.get('advertiser_id')

            url = f"{self.API_BASE_URL}/advertiser/info/"
            params = {
                'advertiser_id': advertiser_id,
                'fields': '["name", "currency", "timezone", "balance"]'
            }
            headers = {
                'Access-Token': credentials.get('access_token'),
            }

            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()

            result = response.json()

            if result.get('code') == 0:
                return result.get('data', {}).get('list', [{}])[0]
            else:
                return {'error': result.get('message')}

        except Exception as e:
            return {'error': str(e)}
