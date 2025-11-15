"""
Base adapter class for plugin integrations
Defines the standard interface for all platform plugins
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AuthResponse:
    """Response from OAuth authentication"""
    success: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class WebhookEvent:
    """Standardized webhook event"""
    event_type: str
    event_id: str
    data: Dict[str, Any]
    timestamp: datetime
    raw_payload: Dict[str, Any]


@dataclass
class SyncResult:
    """Result of synchronization operation"""
    success: bool
    records_fetched: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    error: Optional[str] = None
    details: Dict[str, Any] = None


class BasePluginAdapter(ABC):
    """
    Abstract base class for all plugin adapters.
    Each platform (Google Ads, Meta Ads, TikTok Ads, Shopify) must implement this interface.
    """

    def __init__(self, plugin):
        """
        Initialize the adapter with a plugin instance

        Args:
            plugin: Plugin model instance containing credentials and config
        """
        self.plugin = plugin

    @abstractmethod
    def get_oauth_url(self, redirect_uri: str, state: str) -> str:
        """
        Generate OAuth authorization URL

        Args:
            redirect_uri: Callback URL after authorization
            state: Random state parameter for CSRF protection

        Returns:
            OAuth authorization URL
        """
        pass

    @abstractmethod
    def exchange_code_for_token(self, code: str, redirect_uri: str) -> AuthResponse:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code from OAuth callback
            redirect_uri: Same redirect URI used in authorization

        Returns:
            AuthResponse with tokens and expiration
        """
        pass

    @abstractmethod
    def refresh_access_token(self) -> AuthResponse:
        """
        Refresh the access token using refresh token

        Returns:
            AuthResponse with new access token
        """
        pass

    @abstractmethod
    def verify_connection(self) -> tuple[bool, str]:
        """
        Verify that the connection is working

        Returns:
            Tuple of (success: bool, message: str)
        """
        pass

    @abstractmethod
    def parse_webhook_event(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Optional[WebhookEvent]:
        """
        Parse and validate incoming webhook event

        Args:
            payload: Webhook payload from platform
            headers: HTTP headers from webhook request

        Returns:
            WebhookEvent if valid, None if invalid/unverified
        """
        pass

    @abstractmethod
    def sync_data(self, sync_type: str, **kwargs) -> SyncResult:
        """
        Synchronize data from platform

        Args:
            sync_type: Type of data to sync (e.g., 'campaigns', 'orders')
            **kwargs: Additional parameters for sync

        Returns:
            SyncResult with sync statistics
        """
        pass

    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information from platform

        Returns:
            Dictionary with account details
        """
        pass

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature (default implementation)
        Override in child classes if platform uses different verification

        Args:
            payload: Raw webhook payload bytes
            signature: Signature from webhook headers

        Returns:
            True if signature is valid
        """
        import hmac
        import hashlib

        if not self.plugin.webhook_secret:
            return False

        expected_signature = hmac.new(
            self.plugin.webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    def _check_token_expiration(self):
        """
        Check if token is expired and refresh if needed
        """
        if self.plugin.is_token_expired():
            result = self.refresh_access_token()
            if result.success:
                # Update plugin with new tokens
                from integrations.services.encryption import encrypt_value, decrypt_value
                self.plugin.access_token = encrypt_value(result.access_token)
                if result.refresh_token:
                    self.plugin.refresh_token = encrypt_value(result.refresh_token)
                self.plugin.token_expires_at = result.expires_at
                self.plugin.status = 'connected'
                self.plugin.save()
            else:
                self.plugin.status = 'error'
                self.plugin.last_error = f"Token refresh failed: {result.error}"
                self.plugin.save()
                raise Exception(f"Failed to refresh token: {result.error}")

    def get_decrypted_credentials(self) -> Dict[str, str]:
        """
        Get decrypted credentials from plugin

        Returns:
            Dictionary with decrypted credential values
        """
        from integrations.services.encryption import decrypt_value

        credentials = {}
        if self.plugin.client_id:
            credentials['client_id'] = decrypt_value(self.plugin.client_id)
        if self.plugin.client_secret:
            credentials['client_secret'] = decrypt_value(self.plugin.client_secret)
        if self.plugin.access_token:
            credentials['access_token'] = decrypt_value(self.plugin.access_token)
        if self.plugin.refresh_token:
            credentials['refresh_token'] = decrypt_value(self.plugin.refresh_token)

        return credentials
