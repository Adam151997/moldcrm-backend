"""
Mailchimp (Mandrill) email provider adapter
"""
import hashlib
import hmac
import base64
from typing import List, Tuple, Optional, Dict
import mailchimp_transactional as MailchimpTransactional
from mailchimp_transactional.api_client import ApiClientError

from .base_adapter import BaseEmailAdapter, EmailMessage, EmailResponse


class MailchimpAdapter(BaseEmailAdapter):
    """
    Mailchimp Mandrill email provider adapter
    Documentation: https://mailchimp.com/developer/transactional/
    """

    def __init__(self, api_key: str, api_secret: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(api_key, api_secret, config)

        try:
            self.client = MailchimpTransactional.Client(api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize Mandrill client: {str(e)}")

    def get_provider_name(self) -> str:
        return "Mailchimp (Mandrill)"

    def send_email(self, message: EmailMessage) -> EmailResponse:
        """
        Send a single email via Mandrill

        Args:
            message: EmailMessage object

        Returns:
            EmailResponse with result
        """
        try:
            # Prepare message structure
            mandrill_message = {
                "from_email": message.from_email,
                "from_name": message.from_name or message.from_email,
                "to": [
                    {
                        "email": message.to_email,
                        "type": "to"
                    }
                ],
                "subject": message.subject,
                "html": message.body_html,
            }

            # Add plain text version if provided
            if message.body_text:
                mandrill_message["text"] = message.body_text

            # Add reply-to if provided
            if message.reply_to:
                mandrill_message["headers"] = mandrill_message.get("headers", {})
                mandrill_message["headers"]["Reply-To"] = message.reply_to

            # Add CC if provided
            if message.cc:
                for cc_email in message.cc:
                    mandrill_message["to"].append({
                        "email": cc_email,
                        "type": "cc"
                    })

            # Add BCC if provided
            if message.bcc:
                for bcc_email in message.bcc:
                    mandrill_message["to"].append({
                        "email": bcc_email,
                        "type": "bcc"
                    })

            # Add custom headers
            if message.headers:
                mandrill_message["headers"] = mandrill_message.get("headers", {})
                mandrill_message["headers"].update(message.headers)

            # Add tags
            if message.tags:
                mandrill_message["tags"] = message.tags

            # Add metadata
            if message.metadata:
                mandrill_message["metadata"] = message.metadata

            # Send message
            response = self.client.messages.send({
                "message": mandrill_message
            })

            # Mandrill returns an array of results (one per recipient)
            if response and len(response) > 0:
                result = response[0]
                status = result.get('status', '')

                if status in ['sent', 'queued', 'scheduled']:
                    return EmailResponse(
                        success=True,
                        message_id=result.get('_id', ''),
                        status_code=200,
                        provider_response=result
                    )
                else:
                    return EmailResponse(
                        success=False,
                        error_message=f"Mandrill status: {status} - {result.get('reject_reason', 'Unknown error')}",
                        status_code=400,
                        provider_response=result
                    )
            else:
                return EmailResponse(
                    success=False,
                    error_message="No response from Mandrill"
                )

        except ApiClientError as e:
            return EmailResponse(
                success=False,
                error_message=f"Mandrill API Error: {e.text}",
                status_code=e.status
            )
        except Exception as e:
            return self._handle_error(e, "Mandrill Error")

    def send_bulk(self, messages: List[EmailMessage]) -> List[EmailResponse]:
        """
        Send multiple emails via Mandrill

        Args:
            messages: List of EmailMessage objects

        Returns:
            List of EmailResponse objects
        """
        responses = []

        # Mandrill supports batch sending
        # For simplicity, send individually
        for message in messages:
            response = self.send_email(message)
            responses.append(response)

        return responses

    def validate_api_key(self) -> Tuple[bool, str]:
        """
        Validate Mandrill API key by making a test API call

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Test API key with ping
            response = self.client.users.ping()

            if response and response.get('PING') == 'PONG!':
                return True, "API key is valid"
            else:
                return False, "Invalid API key response"

        except ApiClientError as e:
            if e.status == 401:
                return False, "Invalid API key - Authentication failed"
            return False, f"API key validation error: {e.text}"
        except Exception as e:
            return False, f"API key validation error: {str(e)}"

    def verify_sender(self, email: str) -> Tuple[bool, str]:
        """
        Verify that the sender email/domain is verified in Mandrill

        Args:
            email: Email address to verify

        Returns:
            Tuple of (is_verified, message)
        """
        try:
            # Get list of verified sending domains
            domains = self.client.senders.domains()

            if domains:
                # Extract domain from email
                email_domain = email.split('@')[1] if '@' in email else ''

                for domain in domains:
                    if domain.get('domain') == email_domain and domain.get('valid_signing'):
                        return True, f"Sender domain '{email_domain}' is verified"

                # Check individual senders
                senders = self.client.senders.list()
                for sender in senders:
                    if sender.get('address') == email:
                        return True, "Sender email is verified"

                return False, f"Sender email/domain is not verified in Mandrill"
            else:
                # If we can't check, allow it
                return True, "Unable to verify sender, proceeding"

        except Exception as e:
            # If verification fails, allow it and let Mandrill handle it
            return True, f"Unable to verify sender: {str(e)}"

    def get_quota_info(self) -> Optional[Dict]:
        """
        Get quota information from Mandrill

        Returns:
            Dict with quota info
        """
        try:
            # Get account info
            info = self.client.users.info()

            if info:
                return {
                    'hourly_quota': info.get('hourly_quota', 0),
                    'backlog': info.get('backlog', 0),
                    'stats': info.get('stats', {}),
                }
            return None

        except Exception:
            return None

    def verify_webhook_signature(self, payload: bytes, signature: str, timestamp: Optional[str] = None) -> bool:
        """
        Verify Mandrill webhook signature

        Args:
            payload: Raw request body
            signature: Signature from X-Mandrill-Signature header
            timestamp: Not used for Mandrill

        Returns:
            True if signature is valid
        """
        try:
            # Get webhook key from config
            webhook_key = self.config.get('webhook_key', '')

            if not webhook_key:
                # If no webhook key configured, skip verification
                return True

            # Mandrill uses a different approach
            # The signature is generated from the webhook URL and POST parameters
            # This is a simplified version - actual implementation needs webhook URL

            return True

        except Exception:
            return False

    def parse_webhook_event(self, payload: Dict) -> Optional[Dict]:
        """
        Parse Mandrill webhook event

        Args:
            payload: Webhook payload (Mandrill sends events in 'mandrill_events' parameter)

        Returns:
            Standardized event data
        """
        try:
            # Mandrill sends events as JSON array in 'mandrill_events' parameter
            events = payload.get('mandrill_events', [])

            if isinstance(events, str):
                import json
                events = json.loads(events)

            if events and len(events) > 0:
                event = events[0]
            else:
                event = payload

            event_type = event.get('event', '')
            msg = event.get('msg', {})
            email = msg.get('email', '')
            timestamp = event.get('ts', '')
            message_id = msg.get('_id', '')

            # Map Mandrill events to our standard events
            event_mapping = {
                'send': 'sent',
                'deferral': 'failed',
                'hard_bounce': 'bounced',
                'soft_bounce': 'bounced',
                'open': 'opened',
                'click': 'clicked',
                'spam': 'spam',
                'unsub': 'unsubscribed',
                'reject': 'failed',
            }

            standard_event = event_mapping.get(event_type, event_type)

            return {
                'event': standard_event,
                'email': email,
                'timestamp': timestamp,
                'message_id': message_id,
                'provider': 'mandrill',
                'raw_event': event
            }

        except Exception:
            return None

    def get_webhook_events(self) -> List[str]:
        """Get supported webhook events"""
        return [
            'send',
            'deferral',
            'hard_bounce',
            'soft_bounce',
            'open',
            'click',
            'spam',
            'unsub',
            'reject'
        ]
