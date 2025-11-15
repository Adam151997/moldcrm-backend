"""
Plugin Service - Orchestrator for managing plugin integrations
Handles plugin lifecycle, adapter routing, and credential management
"""
from typing import Optional, Type
from django.core.exceptions import ValidationError
from django.conf import settings
import os

from integrations.models import Plugin
from integrations.services.encryption import encrypt_value, decrypt_value
from .base_adapter import BasePluginAdapter
from .google_ads_adapter import GoogleAdsAdapter
from .meta_ads_adapter import MetaAdsAdapter
from .tiktok_ads_adapter import TikTokAdsAdapter
from .shopify_adapter import ShopifyAdapter


class PluginService:
    """
    Service for managing plugin integrations
    Routes operations to appropriate platform adapters
    """

    # Mapping of plugin types to adapter classes
    ADAPTER_MAP = {
        'google_ads': GoogleAdsAdapter,
        'meta_ads': MetaAdsAdapter,
        'tiktok_ads': TikTokAdsAdapter,
        'shopify': ShopifyAdapter,
    }

    # Category mapping
    CATEGORY_MAP = {
        'google_ads': 'advertising',
        'meta_ads': 'advertising',
        'tiktok_ads': 'advertising',
        'shopify': 'ecommerce',
    }

    # Centralized OAuth credentials from environment variables
    # If set, these will be used instead of user-provided credentials
    CENTRALIZED_CREDENTIALS = {
        'google_ads': {
            'client_id': os.getenv('GOOGLE_ADS_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_ADS_CLIENT_SECRET'),
        },
        'meta_ads': {
            'client_id': os.getenv('META_ADS_CLIENT_ID'),
            'client_secret': os.getenv('META_ADS_CLIENT_SECRET'),
        },
        'tiktok_ads': {
            'client_id': os.getenv('TIKTOK_ADS_CLIENT_ID'),
            'client_secret': os.getenv('TIKTOK_ADS_CLIENT_SECRET'),
        },
        'shopify': {
            'client_id': os.getenv('SHOPIFY_CLIENT_ID'),
            'client_secret': os.getenv('SHOPIFY_CLIENT_SECRET'),
        },
    }

    @classmethod
    def use_centralized_credentials(cls, plugin_type: str) -> bool:
        """
        Check if centralized credentials are configured for this plugin type

        Args:
            plugin_type: Type of plugin

        Returns:
            True if centralized credentials exist
        """
        creds = cls.CENTRALIZED_CREDENTIALS.get(plugin_type, {})
        return bool(creds.get('client_id') and creds.get('client_secret'))

    @classmethod
    def get_oauth_credentials(cls, plugin: Plugin) -> dict:
        """
        Get OAuth credentials - either centralized or user-provided

        Args:
            plugin: Plugin instance

        Returns:
            Dictionary with client_id and client_secret
        """
        # Check if centralized credentials are available
        if cls.use_centralized_credentials(plugin.plugin_type):
            creds = cls.CENTRALIZED_CREDENTIALS[plugin.plugin_type]
            return {
                'client_id': creds['client_id'],
                'client_secret': creds['client_secret']
            }

        # Fall back to user-provided credentials
        from integrations.services.encryption import decrypt_value

        if not plugin.client_id or not plugin.client_secret:
            raise ValueError(
                f"No credentials configured for {plugin.get_plugin_type_display()}. "
                "Either set environment variables or provide credentials."
            )

        return {
            'client_id': decrypt_value(plugin.client_id),
            'client_secret': decrypt_value(plugin.client_secret)
        }

    @classmethod
    def get_adapter(cls, plugin: Plugin) -> BasePluginAdapter:
        """
        Get the appropriate adapter instance for a plugin

        Args:
            plugin: Plugin instance

        Returns:
            Adapter instance

        Raises:
            ValueError: If plugin type is not supported
        """
        adapter_class = cls.ADAPTER_MAP.get(plugin.plugin_type)
        if not adapter_class:
            raise ValueError(f"Unsupported plugin type: {plugin.plugin_type}")

        return adapter_class(plugin)

    @classmethod
    def create_plugin(cls, account, plugin_type: str, name: str,
                     client_id: str = None, client_secret: str = None, config: dict = None) -> Plugin:
        """
        Create a new plugin with optional encrypted credentials
        If centralized credentials exist, client_id/client_secret are optional

        Args:
            account: Account instance
            plugin_type: Type of plugin
            name: User-friendly name
            client_id: OAuth client ID (optional if centralized credentials exist)
            client_secret: OAuth client secret (optional if centralized credentials exist)
            config: Platform-specific configuration

        Returns:
            Created Plugin instance
        """
        # Validate plugin type
        if plugin_type not in cls.ADAPTER_MAP:
            raise ValueError(f"Unsupported plugin type: {plugin_type}")

        # Check if centralized credentials are available
        use_centralized = cls.use_centralized_credentials(plugin_type)

        # If not using centralized, require user credentials
        if not use_centralized and (not client_id or not client_secret):
            raise ValueError(
                f"OAuth credentials required for {plugin_type}. "
                "Please provide client_id and client_secret."
            )

        # Get category
        category = cls.CATEGORY_MAP.get(plugin_type, 'other')

        # Encrypt user-provided credentials only if provided
        encrypted_client_id = encrypt_value(client_id) if client_id else ''
        encrypted_client_secret = encrypt_value(client_secret) if client_secret else ''

        # Create plugin
        plugin = Plugin.objects.create(
            account=account,
            plugin_type=plugin_type,
            name=name,
            category=category,
            client_id=encrypted_client_id,
            client_secret=encrypted_client_secret,
            config=config or {},
            status='pending'
        )

        return plugin

    @classmethod
    def update_credentials(cls, plugin: Plugin, **credentials):
        """
        Update plugin credentials (encrypts automatically)

        Args:
            plugin: Plugin instance
            **credentials: Credential fields to update (client_id, client_secret, access_token, refresh_token)
        """
        if 'client_id' in credentials:
            plugin.client_id = encrypt_value(credentials['client_id'])

        if 'client_secret' in credentials:
            plugin.client_secret = encrypt_value(credentials['client_secret'])

        if 'access_token' in credentials:
            plugin.access_token = encrypt_value(credentials['access_token'])

        if 'refresh_token' in credentials:
            plugin.refresh_token = encrypt_value(credentials['refresh_token'])

        plugin.save()

    @classmethod
    def initiate_oauth(cls, plugin: Plugin, redirect_uri: str, state: str) -> str:
        """
        Initiate OAuth flow for a plugin

        Args:
            plugin: Plugin instance
            redirect_uri: OAuth callback URL
            state: Random state for CSRF protection

        Returns:
            OAuth authorization URL
        """
        adapter = cls.get_adapter(plugin)
        return adapter.get_oauth_url(redirect_uri, state)

    @classmethod
    def complete_oauth(cls, plugin: Plugin, code: str, redirect_uri: str) -> tuple[bool, str]:
        """
        Complete OAuth flow by exchanging code for tokens

        Args:
            plugin: Plugin instance
            code: Authorization code
            redirect_uri: OAuth callback URL

        Returns:
            Tuple of (success, message)
        """
        try:
            adapter = cls.get_adapter(plugin)
            result = adapter.exchange_code_for_token(code, redirect_uri)

            if result.success:
                # Update plugin with tokens
                plugin.access_token = encrypt_value(result.access_token)
                if result.refresh_token:
                    plugin.refresh_token = encrypt_value(result.refresh_token)
                plugin.token_expires_at = result.expires_at
                plugin.status = 'connected'
                plugin.is_verified = True
                plugin.save()

                return True, "OAuth completed successfully"
            else:
                plugin.status = 'error'
                plugin.last_error = result.error
                plugin.save()
                return False, result.error

        except Exception as e:
            plugin.status = 'error'
            plugin.last_error = str(e)
            plugin.save()
            return False, str(e)

    @classmethod
    def verify_connection(cls, plugin: Plugin) -> tuple[bool, str]:
        """
        Verify that a plugin connection is working

        Args:
            plugin: Plugin instance

        Returns:
            Tuple of (success, message)
        """
        try:
            adapter = cls.get_adapter(plugin)
            return adapter.verify_connection()
        except Exception as e:
            return False, str(e)

    @classmethod
    def sync_plugin_data(cls, plugin: Plugin, sync_type: str, **kwargs):
        """
        Synchronize data from plugin platform

        Args:
            plugin: Plugin instance
            sync_type: Type of data to sync
            **kwargs: Additional sync parameters

        Returns:
            SyncResult
        """
        from django.utils import timezone
        from integrations.models import PluginSyncLog
        import time

        start_time = time.time()
        sync_log = PluginSyncLog.objects.create(
            plugin=plugin,
            sync_type=sync_type,
            status='failed'  # Default to failed, update on success
        )

        try:
            adapter = cls.get_adapter(plugin)
            result = adapter.sync_data(sync_type, **kwargs)

            # Update sync log
            sync_log.status = 'success' if result.success else 'failed'
            sync_log.records_fetched = result.records_fetched
            sync_log.records_created = result.records_created
            sync_log.records_updated = result.records_updated
            sync_log.records_failed = result.records_failed
            sync_log.error_message = result.error or ''
            sync_log.details = result.details or {}
            sync_log.completed_at = timezone.now()
            sync_log.duration_seconds = time.time() - start_time
            sync_log.save()

            # Update plugin stats
            if result.success:
                plugin.increment_sync_count()
                plugin.last_error = ''
                plugin.error_count = 0
            else:
                plugin.increment_error_count()
                plugin.last_error = result.error

            plugin.save()

            return result

        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.duration_seconds = time.time() - start_time
            sync_log.save()

            plugin.increment_error_count()
            plugin.last_error = str(e)
            plugin.save()

            raise

    @classmethod
    def process_webhook(cls, plugin: Plugin, payload: dict, headers: dict):
        """
        Process incoming webhook from plugin platform

        Args:
            plugin: Plugin instance
            payload: Webhook payload
            headers: HTTP headers

        Returns:
            Parsed WebhookEvent or None
        """
        from integrations.models import PluginEvent
        from django.utils import timezone

        adapter = cls.get_adapter(plugin)
        event = adapter.parse_webhook_event(payload, headers)

        if event:
            # Create PluginEvent record
            plugin_event = PluginEvent.objects.create(
                plugin=plugin,
                event_type=event.event_type,
                event_id=event.event_id,
                payload=event.raw_payload,
                processed_data=event.data,
                status='pending'
            )

            # Process event asynchronously (to be implemented in tasks)
            # from integrations.tasks import process_plugin_event_task
            # process_plugin_event_task.delay(plugin_event.id)

            return plugin_event

        return None

    @classmethod
    def get_account_info(cls, plugin: Plugin) -> dict:
        """
        Get account information from plugin platform

        Args:
            plugin: Plugin instance

        Returns:
            Account information dictionary
        """
        try:
            adapter = cls.get_adapter(plugin)
            return adapter.get_account_info()
        except Exception as e:
            return {'error': str(e)}

    @classmethod
    def refresh_token_if_needed(cls, plugin: Plugin) -> bool:
        """
        Refresh token if it's expired or about to expire

        Args:
            plugin: Plugin instance

        Returns:
            True if refresh was successful or not needed
        """
        try:
            if plugin.is_token_expired():
                adapter = cls.get_adapter(plugin)
                result = adapter.refresh_access_token()

                if result.success:
                    plugin.access_token = encrypt_value(result.access_token)
                    if result.refresh_token:
                        plugin.refresh_token = encrypt_value(result.refresh_token)
                    plugin.token_expires_at = result.expires_at
                    plugin.status = 'connected'
                    plugin.save()
                    return True
                else:
                    plugin.status = 'error'
                    plugin.last_error = f"Token refresh failed: {result.error}"
                    plugin.save()
                    return False

            return True  # Token not expired

        except Exception as e:
            plugin.status = 'error'
            plugin.last_error = str(e)
            plugin.save()
            return False
