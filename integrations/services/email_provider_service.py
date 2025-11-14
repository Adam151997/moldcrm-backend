"""
Unified email provider service
Orchestrates sending emails through multiple providers
"""
from typing import List, Optional, Dict, Tuple
from django.utils import timezone
from datetime import timedelta

from integrations.models import EmailProvider, Email, EmailCampaign
from .encryption import decrypt_api_key
from .adapters.base_adapter import BaseEmailAdapter, EmailMessage, EmailResponse
from .adapters.sendgrid_adapter import SendGridAdapter
from .adapters.mailgun_adapter import MailgunAdapter
from .adapters.brevo_adapter import BrevoAdapter
from .adapters.mailchimp_adapter import MailchimpAdapter
from .adapters.klaviyo_adapter import KlaviyoAdapter


class EmailProviderService:
    """
    Service for managing and using email providers
    """

    # Map provider types to adapter classes
    ADAPTER_MAP = {
        'sendgrid': SendGridAdapter,
        'mailgun': MailgunAdapter,
        'mailchimp': MailchimpAdapter,
        'brevo': BrevoAdapter,
        'klaviyo': KlaviyoAdapter,
    }

    @classmethod
    def get_adapter(cls, provider: EmailProvider) -> Optional[BaseEmailAdapter]:
        """
        Get adapter instance for a provider

        Args:
            provider: EmailProvider model instance

        Returns:
            Adapter instance or None
        """
        adapter_class = cls.ADAPTER_MAP.get(provider.provider_type)

        if not adapter_class:
            return None

        try:
            # Decrypt API keys
            api_key = decrypt_api_key(provider.api_key)
            api_secret = decrypt_api_key(provider.api_secret) if provider.api_secret else None

            # Create adapter instance
            adapter = adapter_class(
                api_key=api_key,
                api_secret=api_secret,
                config=provider.config
            )

            return adapter

        except Exception as e:
            print(f"Error creating adapter for {provider.name}: {str(e)}")
            return None

    @classmethod
    def validate_provider(cls, provider: EmailProvider) -> Tuple[bool, str]:
        """
        Validate a provider's API key and configuration

        Args:
            provider: EmailProvider model instance

        Returns:
            Tuple of (is_valid, message)
        """
        adapter = cls.get_adapter(provider)

        if not adapter:
            return False, "Failed to create adapter for provider"

        # Validate API key
        is_valid, message = adapter.validate_api_key()

        if not is_valid:
            return False, message

        # Verify sender email
        is_verified, sender_message = adapter.verify_sender(provider.sender_email)

        if not is_verified:
            return False, sender_message

        return True, "Provider validated successfully"

    @classmethod
    def send_email(cls, provider: EmailProvider, email_data: Dict) -> EmailResponse:
        """
        Send a single email through a provider

        Args:
            provider: EmailProvider model instance
            email_data: Dictionary with email details

        Returns:
            EmailResponse
        """
        # Check if provider is active
        if not provider.is_active:
            return EmailResponse(
                success=False,
                error_message="Provider is not active"
            )

        # Check quota
        quota_ok, quota_message = provider.check_quota()
        if not quota_ok:
            return EmailResponse(
                success=False,
                error_message=quota_message
            )

        # Get adapter
        adapter = cls.get_adapter(provider)
        if not adapter:
            return EmailResponse(
                success=False,
                error_message="Failed to create adapter"
            )

        # Create email message
        message = EmailMessage(
            to_email=email_data.get('to_email'),
            subject=email_data.get('subject'),
            body_html=email_data.get('body_html'),
            body_text=email_data.get('body_text', ''),
            from_email=email_data.get('from_email', provider.sender_email),
            from_name=email_data.get('from_name', provider.sender_name),
            reply_to=email_data.get('reply_to'),
            cc=email_data.get('cc'),
            bcc=email_data.get('bcc'),
            headers=email_data.get('headers'),
            tags=email_data.get('tags'),
            metadata=email_data.get('metadata')
        )

        # Send email
        response = adapter.send_email(message)

        # Update provider stats
        if response.success:
            provider.increment_sent_count()
            provider.last_error = ""
        else:
            provider.last_error = response.error_message
            provider.save(update_fields=['last_error'])

        return response

    @classmethod
    def send_bulk(cls, provider: EmailProvider, emails_data: List[Dict]) -> List[EmailResponse]:
        """
        Send multiple emails through a provider

        Args:
            provider: EmailProvider model instance
            emails_data: List of email data dictionaries

        Returns:
            List of EmailResponse objects
        """
        # Check if provider is active
        if not provider.is_active:
            return [EmailResponse(
                success=False,
                error_message="Provider is not active"
            ) for _ in emails_data]

        # Get adapter
        adapter = cls.get_adapter(provider)
        if not adapter:
            return [EmailResponse(
                success=False,
                error_message="Failed to create adapter"
            ) for _ in emails_data]

        # Create email messages
        messages = []
        for email_data in emails_data:
            message = EmailMessage(
                to_email=email_data.get('to_email'),
                subject=email_data.get('subject'),
                body_html=email_data.get('body_html'),
                body_text=email_data.get('body_text', ''),
                from_email=email_data.get('from_email', provider.sender_email),
                from_name=email_data.get('from_name', provider.sender_name),
                reply_to=email_data.get('reply_to'),
                cc=email_data.get('cc'),
                bcc=email_data.get('bcc'),
                headers=email_data.get('headers'),
                tags=email_data.get('tags'),
                metadata=email_data.get('metadata')
            )
            messages.append(message)

        # Send bulk
        responses = adapter.send_bulk(messages)

        # Update provider stats
        success_count = sum(1 for r in responses if r.success)
        for _ in range(success_count):
            provider.increment_sent_count()

        return responses

    @classmethod
    def get_available_provider(cls, account, providers: List[EmailProvider] = None) -> Optional[EmailProvider]:
        """
        Get an available provider based on quota and priority

        Args:
            account: Account instance
            providers: Optional list of providers to choose from

        Returns:
            EmailProvider instance or None
        """
        if providers is None:
            providers = EmailProvider.objects.filter(
                account=account,
                is_active=True,
                is_verified=True
            ).order_by('priority')

        for provider in providers:
            quota_ok, _ = provider.check_quota()
            if quota_ok:
                return provider

        return None

    @classmethod
    def send_with_strategy(cls, campaign: EmailCampaign, email_data: Dict) -> EmailResponse:
        """
        Send email using campaign's provider strategy

        Args:
            campaign: EmailCampaign instance
            email_data: Email data dictionary

        Returns:
            EmailResponse
        """
        providers = list(campaign.providers.filter(
            is_active=True,
            is_verified=True
        ).order_by('priority'))

        if not providers:
            return EmailResponse(
                success=False,
                error_message="No active providers configured for campaign"
            )

        strategy = campaign.provider_strategy

        if strategy == 'priority':
            # Try providers in priority order
            for provider in providers:
                quota_ok, _ = provider.check_quota()
                if quota_ok:
                    response = cls.send_email(provider, email_data)
                    if response.success:
                        return response
                    # Continue to next provider if failed

            return EmailResponse(
                success=False,
                error_message="All providers failed or quota exceeded"
            )

        elif strategy == 'round_robin':
            # Distribute load across providers
            # Simple implementation: use provider with lowest sent count
            provider = min(providers, key=lambda p: p.sent_today)
            quota_ok, quota_message = provider.check_quota()

            if not quota_ok:
                # Fallback to any available provider
                provider = cls.get_available_provider(campaign.account, providers)
                if not provider:
                    return EmailResponse(
                        success=False,
                        error_message="All providers quota exceeded"
                    )

            return cls.send_email(provider, email_data)

        elif strategy == 'failover':
            # Use first provider, failover only on error
            primary_provider = providers[0]
            quota_ok, _ = primary_provider.check_quota()

            if quota_ok:
                response = cls.send_email(primary_provider, email_data)
                if response.success:
                    return response

            # Failover to other providers
            for provider in providers[1:]:
                quota_ok, _ = provider.check_quota()
                if quota_ok:
                    response = cls.send_email(provider, email_data)
                    if response.success:
                        return response

            return EmailResponse(
                success=False,
                error_message="Primary and failover providers failed"
            )

        return EmailResponse(
            success=False,
            error_message=f"Unknown strategy: {strategy}"
        )

    @classmethod
    def reset_daily_counters(cls):
        """
        Reset daily sent counters for all providers
        Should be run as a daily cron job
        """
        EmailProvider.objects.all().update(sent_today=0)

    @classmethod
    def reset_monthly_counters(cls):
        """
        Reset monthly sent counters for all providers
        Should be run as a monthly cron job
        """
        EmailProvider.objects.all().update(sent_this_month=0)

    @classmethod
    def get_provider_stats(cls, provider: EmailProvider) -> Dict:
        """
        Get statistics for a provider

        Args:
            provider: EmailProvider instance

        Returns:
            Dictionary with stats
        """
        # Get adapter
        adapter = cls.get_adapter(provider)

        # Get quota info from provider API
        quota_info = None
        if adapter:
            quota_info = adapter.get_quota_info()

        # Get stats from database
        total_sent = Email.objects.filter(provider=provider).count()
        delivered = Email.objects.filter(provider=provider, status='delivered').count()
        opened = Email.objects.filter(provider=provider, status='opened').count()
        clicked = Email.objects.filter(provider=provider, status='clicked').count()
        bounced = Email.objects.filter(provider=provider, status='bounced').count()
        failed = Email.objects.filter(provider=provider, status='failed').count()

        return {
            'total_sent': total_sent,
            'delivered': delivered,
            'opened': opened,
            'clicked': clicked,
            'bounced': bounced,
            'failed': failed,
            'sent_today': provider.sent_today,
            'sent_this_month': provider.sent_this_month,
            'quota_info': quota_info,
            'delivery_rate': (delivered / total_sent * 100) if total_sent > 0 else 0,
            'open_rate': (opened / delivered * 100) if delivered > 0 else 0,
            'click_rate': (clicked / delivered * 100) if delivered > 0 else 0,
            'bounce_rate': (bounced / total_sent * 100) if total_sent > 0 else 0,
        }
