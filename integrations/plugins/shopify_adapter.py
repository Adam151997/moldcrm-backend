"""
Shopify plugin adapter
Handles OAuth, webhooks, and data synchronization for Shopify e-commerce platform
"""
import requests
import hmac
import hashlib
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.utils import timezone

from .base_adapter import BasePluginAdapter, AuthResponse, WebhookEvent, SyncResult


class ShopifyAdapter(BasePluginAdapter):
    """
    Adapter for Shopify integration
    Implements OAuth 2.0 flow and Shopify Admin API integration
    """

    # Shopify OAuth and API endpoints are shop-specific
    API_VERSION = "2024-01"

    # Required scopes
    SCOPES = [
        "read_orders",
        "read_customers",
        "read_products",
        "read_fulfillments",
        "read_inventory",
    ]

    def _get_shop_url(self) -> str:
        """Get shop URL from config"""
        shop_domain = self.plugin.config.get('shop_domain', '')
        if not shop_domain:
            raise ValueError("Shop domain not configured")
        if not shop_domain.endswith('.myshopify.com'):
            shop_domain = f"{shop_domain}.myshopify.com"
        return shop_domain

    def _get_api_base_url(self) -> str:
        """Get API base URL for the shop"""
        shop_url = self._get_shop_url()
        return f"https://{shop_url}/admin/api/{self.API_VERSION}"

    def get_oauth_url(self, redirect_uri: str, state: str) -> str:
        """Generate Shopify OAuth authorization URL"""
        credentials = self.get_decrypted_credentials()
        client_id = credentials.get('client_id')
        shop_url = self._get_shop_url()

        params = {
            'client_id': client_id,
            'scope': ','.join(self.SCOPES),
            'redirect_uri': redirect_uri,
            'state': state,
        }

        query_string = '&'.join([f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()])
        return f"https://{shop_url}/admin/oauth/authorize?{query_string}"

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> AuthResponse:
        """Exchange authorization code for access token"""
        try:
            credentials = self.get_decrypted_credentials()
            shop_url = self._get_shop_url()

            data = {
                'client_id': credentials.get('client_id'),
                'client_secret': credentials.get('client_secret'),
                'code': code,
            }

            url = f"https://{shop_url}/admin/oauth/access_token"
            response = requests.post(url, json=data)
            response.raise_for_status()

            token_data = response.json()

            # Shopify access tokens don't expire
            return AuthResponse(
                success=True,
                access_token=token_data.get('access_token'),
                refresh_token=None,  # Shopify tokens don't expire, no refresh needed
                expires_at=None
            )

        except Exception as e:
            return AuthResponse(
                success=False,
                error=str(e)
            )

    def refresh_access_token(self) -> AuthResponse:
        """
        Refresh the access token
        Note: Shopify access tokens don't expire, so no refresh needed
        """
        credentials = self.get_decrypted_credentials()
        return AuthResponse(
            success=True,
            access_token=credentials.get('access_token'),
            refresh_token=None,
            expires_at=None
        )

    def verify_connection(self) -> tuple[bool, str]:
        """Verify that the Shopify connection is working"""
        try:
            credentials = self.get_decrypted_credentials()
            api_base_url = self._get_api_base_url()

            # Test API call to get shop info
            headers = {
                'X-Shopify-Access-Token': credentials.get('access_token'),
            }

            url = f"{api_base_url}/shop.json"
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            shop_data = response.json().get('shop', {})
            shop_name = shop_data.get('name', 'Unknown')

            return True, f"Connected to {shop_name}"

        except Exception as e:
            return False, f"Connection verification failed: {str(e)}"

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Shopify webhook signature using HMAC"""
        if not self.plugin.client_secret:
            return False

        from integrations.services.encryption import decrypt_value
        client_secret = decrypt_value(self.plugin.client_secret)

        # Shopify uses base64-encoded HMAC-SHA256
        expected_signature = base64.b64encode(
            hmac.new(
                client_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).digest()
        ).decode('utf-8')

        return hmac.compare_digest(expected_signature, signature)

    def parse_webhook_event(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Optional[WebhookEvent]:
        """
        Parse Shopify webhook event
        """
        try:
            # Verify signature
            signature = headers.get('X-Shopify-Hmac-Sha256', '')
            if signature and not self.verify_webhook_signature(
                str(payload).encode('utf-8'),
                signature
            ):
                return None

            # Get event topic from header
            topic = headers.get('X-Shopify-Topic', '')

            # Determine event type
            event_type = f"shopify.{topic.replace('/', '.')}"
            event_id = str(payload.get('id', ''))

            return WebhookEvent(
                event_type=event_type,
                event_id=event_id,
                data=payload,
                timestamp=datetime.fromisoformat(payload.get('created_at', timezone.now().isoformat()).replace('Z', '+00:00')),
                raw_payload=payload
            )

        except Exception:
            return None

    def sync_data(self, sync_type: str, **kwargs) -> SyncResult:
        """
        Synchronize data from Shopify

        Supported sync types:
        - orders: Sync order data
        - customers: Sync customer data
        - products: Sync product data
        """
        try:
            if sync_type == 'orders':
                return self._sync_orders(**kwargs)
            elif sync_type == 'customers':
                return self._sync_customers(**kwargs)
            elif sync_type == 'products':
                return self._sync_products(**kwargs)
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

    def _sync_orders(self, **kwargs) -> SyncResult:
        """Sync order data from Shopify"""
        try:
            credentials = self.get_decrypted_credentials()
            api_base_url = self._get_api_base_url()

            headers = {
                'X-Shopify-Access-Token': credentials.get('access_token'),
            }

            params = {
                'status': kwargs.get('status', 'any'),
                'limit': kwargs.get('limit', 250),
            }

            url = f"{api_base_url}/orders.json"
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            orders = data.get('orders', [])

            return SyncResult(
                success=True,
                records_fetched=len(orders),
                details={'orders': orders}
            )

        except Exception as e:
            return SyncResult(
                success=False,
                error=str(e)
            )

    def _sync_customers(self, **kwargs) -> SyncResult:
        """Sync customer data from Shopify"""
        try:
            credentials = self.get_decrypted_credentials()
            api_base_url = self._get_api_base_url()

            headers = {
                'X-Shopify-Access-Token': credentials.get('access_token'),
            }

            params = {
                'limit': kwargs.get('limit', 250),
            }

            url = f"{api_base_url}/customers.json"
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            customers = data.get('customers', [])

            return SyncResult(
                success=True,
                records_fetched=len(customers),
                details={'customers': customers}
            )

        except Exception as e:
            return SyncResult(
                success=False,
                error=str(e)
            )

    def _sync_products(self, **kwargs) -> SyncResult:
        """Sync product data from Shopify"""
        try:
            credentials = self.get_decrypted_credentials()
            api_base_url = self._get_api_base_url()

            headers = {
                'X-Shopify-Access-Token': credentials.get('access_token'),
            }

            params = {
                'limit': kwargs.get('limit', 250),
            }

            url = f"{api_base_url}/products.json"
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            products = data.get('products', [])

            return SyncResult(
                success=True,
                records_fetched=len(products),
                details={'products': products}
            )

        except Exception as e:
            return SyncResult(
                success=False,
                error=str(e)
            )

    def get_account_info(self) -> Dict[str, Any]:
        """Get Shopify shop information"""
        try:
            credentials = self.get_decrypted_credentials()
            api_base_url = self._get_api_base_url()

            headers = {
                'X-Shopify-Access-Token': credentials.get('access_token'),
            }

            url = f"{api_base_url}/shop.json"
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            return response.json().get('shop', {})

        except Exception as e:
            return {'error': str(e)}

    def register_webhook(self, topic: str, address: str) -> bool:
        """
        Register a webhook with Shopify

        Args:
            topic: Webhook topic (e.g., 'orders/create', 'customers/create')
            address: Webhook callback URL

        Returns:
            True if successful
        """
        try:
            credentials = self.get_decrypted_credentials()
            api_base_url = self._get_api_base_url()

            headers = {
                'X-Shopify-Access-Token': credentials.get('access_token'),
            }

            data = {
                'webhook': {
                    'topic': topic,
                    'address': address,
                    'format': 'json'
                }
            }

            url = f"{api_base_url}/webhooks.json"
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            return True

        except Exception:
            return False
