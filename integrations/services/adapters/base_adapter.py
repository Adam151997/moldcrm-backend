"""
Base adapter interface for email providers
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class EmailMessage:
    """Email message data structure"""
    to_email: str
    subject: str
    body_html: str
    body_text: str = ""
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[Dict]] = None
    headers: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict] = None


@dataclass
class EmailResponse:
    """Response from email provider"""
    success: bool
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    status_code: Optional[int] = None
    provider_response: Optional[Dict] = None


class BaseEmailAdapter(ABC):
    """
    Abstract base class for all email provider adapters

    Each provider (SendGrid, Mailgun, etc.) must implement these methods
    """

    def __init__(self, api_key: str, api_secret: Optional[str] = None, config: Optional[Dict] = None):
        """
        Initialize the adapter with credentials

        Args:
            api_key: API key for the provider
            api_secret: Optional API secret (for providers that need it)
            config: Optional provider-specific configuration
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.config = config or {}

    @abstractmethod
    def send_email(self, message: EmailMessage) -> EmailResponse:
        """
        Send a single email

        Args:
            message: EmailMessage object with email details

        Returns:
            EmailResponse with success status and message ID
        """
        pass

    @abstractmethod
    def send_bulk(self, messages: List[EmailMessage]) -> List[EmailResponse]:
        """
        Send multiple emails (batch sending)

        Args:
            messages: List of EmailMessage objects

        Returns:
            List of EmailResponse objects
        """
        pass

    @abstractmethod
    def validate_api_key(self) -> Tuple[bool, str]:
        """
        Validate that the API key is valid

        Returns:
            Tuple of (is_valid, message)
        """
        pass

    @abstractmethod
    def verify_sender(self, email: str) -> Tuple[bool, str]:
        """
        Verify that the sender email is authorized

        Args:
            email: Email address to verify

        Returns:
            Tuple of (is_verified, message)
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the provider name

        Returns:
            Provider name (e.g., "SendGrid", "Mailgun")
        """
        pass

    def get_quota_info(self) -> Optional[Dict]:
        """
        Get quota information from provider (if available)

        Returns:
            Dict with quota info or None if not supported
        """
        return None

    def supports_bulk_send(self) -> bool:
        """
        Check if provider supports bulk sending

        Returns:
            True if bulk sending is supported
        """
        return True

    def get_webhook_events(self) -> List[str]:
        """
        Get list of webhook events supported by this provider

        Returns:
            List of event names
        """
        return [
            'delivered',
            'opened',
            'clicked',
            'bounced',
            'spam',
            'unsubscribed',
            'failed'
        ]

    def verify_webhook_signature(self, payload: bytes, signature: str, timestamp: Optional[str] = None) -> bool:
        """
        Verify webhook signature for security

        Args:
            payload: Raw request body
            signature: Signature from webhook headers
            timestamp: Optional timestamp for replay protection

        Returns:
            True if signature is valid
        """
        # Default implementation - override in subclass
        return True

    def parse_webhook_event(self, payload: Dict) -> Optional[Dict]:
        """
        Parse webhook event data

        Args:
            payload: Webhook payload

        Returns:
            Standardized event data or None if invalid
        """
        # Default implementation - override in subclass
        return None

    def _handle_error(self, error: Exception, context: str = "") -> EmailResponse:
        """
        Handle errors consistently across adapters

        Args:
            error: The exception that occurred
            context: Context about where the error occurred

        Returns:
            EmailResponse with error details
        """
        error_message = f"{context}: {str(error)}" if context else str(error)
        return EmailResponse(
            success=False,
            error_message=error_message
        )
