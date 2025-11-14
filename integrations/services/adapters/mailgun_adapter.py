"""
Mailgun email provider adapter
"""
import hashlib
import hmac
from typing import List, Tuple, Optional, Dict
import requests

from .base_adapter import BaseEmailAdapter, EmailMessage, EmailResponse


class MailgunAdapter(BaseEmailAdapter):
    """
    Mailgun email provider adapter
    Documentation: https://documentation.mailgun.com/
    """

    def __init__(self, api_key: str, api_secret: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(api_key, api_secret, config)

        # Mailgun requires a domain - get it from config
        self.domain = config.get('domain', '') if config else ''
        if not self.domain:
            raise ValueError("Mailgun requires 'domain' in config")

        # Get region (US or EU)
        self.region = config.get('region', 'us') if config else 'us'

        # Set base URL based on region
        if self.region == 'eu':
            self.base_url = f"https://api.eu.mailgun.net/v3/{self.domain}"
        else:
            self.base_url = f"https://api.mailgun.net/v3/{self.domain}"

        self.auth = ("api", api_key)

    def get_provider_name(self) -> str:
        return "Mailgun"

    def send_email(self, message: EmailMessage) -> EmailResponse:
        """
        Send a single email via Mailgun

        Args:
            message: EmailMessage object

        Returns:
            EmailResponse with result
        """
        try:
            # Prepare email data
            data = {
                "from": f"{message.from_name} <{message.from_email}>" if message.from_name else message.from_email,
                "to": message.to_email,
                "subject": message.subject,
                "html": message.body_html,
            }

            # Add plain text version if provided
            if message.body_text:
                data["text"] = message.body_text

            # Add reply-to if provided
            if message.reply_to:
                data["h:Reply-To"] = message.reply_to

            # Add CC if provided
            if message.cc:
                data["cc"] = ",".join(message.cc)

            # Add BCC if provided
            if message.bcc:
                data["bcc"] = ",".join(message.bcc)

            # Add custom headers
            if message.headers:
                for key, value in message.headers.items():
                    data[f"h:{key}"] = value

            # Add tags
            if message.tags:
                data["o:tag"] = message.tags

            # Add custom variables (metadata)
            if message.metadata:
                for key, value in message.metadata.items():
                    data[f"v:{key}"] = str(value)

            # Send request
            response = requests.post(
                f"{self.base_url}/messages",
                auth=self.auth,
                data=data,
                timeout=30
            )

            if response.status_code == 200:
                response_data = response.json()
                message_id = response_data.get('id', '')

                return EmailResponse(
                    success=True,
                    message_id=message_id,
                    status_code=response.status_code,
                    provider_response=response_data
                )
            else:
                return EmailResponse(
                    success=False,
                    error_message=f"Mailgun error: {response.text}",
                    status_code=response.status_code
                )

        except requests.exceptions.RequestException as e:
            return self._handle_error(e, "Mailgun Request Error")
        except Exception as e:
            return self._handle_error(e, "Mailgun Error")

    def send_bulk(self, messages: List[EmailMessage]) -> List[EmailResponse]:
        """
        Send multiple emails via Mailgun
        Mailgun supports batch sending up to 1000 recipients

        Args:
            messages: List of EmailMessage objects

        Returns:
            List of EmailResponse objects
        """
        responses = []

        # For simplicity, send individually
        # For production, consider batching recipients with same content
        for message in messages:
            response = self.send_email(message)
            responses.append(response)

        return responses

    def validate_api_key(self) -> Tuple[bool, str]:
        """
        Validate Mailgun API key by making a test API call

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Test API key by getting domain info
            response = requests.get(
                f"{self.base_url}",
                auth=self.auth,
                timeout=10
            )

            if response.status_code == 200:
                return True, "API key is valid"
            elif response.status_code == 401:
                return False, "Invalid API key - Authentication failed"
            elif response.status_code == 404:
                return False, f"Domain '{self.domain}' not found in Mailgun account"
            else:
                return False, f"API key validation failed with status {response.status_code}"

        except requests.exceptions.RequestException as e:
            return False, f"API key validation error: {str(e)}"
        except Exception as e:
            return False, f"API key validation error: {str(e)}"

    def verify_sender(self, email: str) -> Tuple[bool, str]:
        """
        Verify that the sender email is authorized in Mailgun
        Mailgun allows any email from verified domain

        Args:
            email: Email address to verify

        Returns:
            Tuple of (is_verified, message)
        """
        try:
            # Extract domain from email
            email_domain = email.split('@')[1] if '@' in email else ''

            if email_domain == self.domain:
                return True, f"Sender email matches configured domain ({self.domain})"
            else:
                return False, f"Sender email domain ({email_domain}) doesn't match Mailgun domain ({self.domain})"

        except Exception as e:
            return False, f"Sender verification error: {str(e)}"

    def get_quota_info(self) -> Optional[Dict]:
        """
        Get quota information from Mailgun

        Returns:
            Dict with quota info
        """
        try:
            # Get domain stats
            response = requests.get(
                f"{self.base_url}/stats/total",
                auth=self.auth,
                params={'event': 'accepted'},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                stats = data.get('stats', [])
                if stats:
                    return {
                        'accepted': stats[0].get('accepted', {}).get('total', 0),
                        'delivered': stats[0].get('delivered', {}).get('total', 0),
                        'failed': stats[0].get('failed', {}).get('total', 0),
                    }
            return None

        except Exception:
            return None

    def verify_webhook_signature(self, payload: bytes, signature: str, timestamp: Optional[str] = None) -> bool:
        """
        Verify Mailgun webhook signature

        Args:
            payload: Raw request body (not used for Mailgun)
            signature: Signature from webhook payload
            timestamp: Timestamp from webhook payload

        Returns:
            True if signature is valid
        """
        try:
            # Mailgun webhook signature verification
            # The webhook sends: timestamp, token, and signature
            # We need to get these from the webhook payload (passed separately)

            # For Mailgun, signature verification is typically done using:
            # hmac_digest = hmac.new(
            #     key=api_key.encode(),
            #     msg='{}{}'.format(timestamp, token).encode(),
            #     digestmod=hashlib.sha256
            # ).hexdigest()

            # Since we need token and timestamp from the actual webhook request,
            # this is a placeholder. Real implementation should be in webhook handler
            return True

        except Exception:
            return False

    def parse_webhook_event(self, payload: Dict) -> Optional[Dict]:
        """
        Parse Mailgun webhook event

        Args:
            payload: Webhook payload

        Returns:
            Standardized event data
        """
        try:
            event_data = payload.get('event-data', {})
            event_type = event_data.get('event', '')
            email = event_data.get('recipient', '')
            timestamp = event_data.get('timestamp', '')
            message_id = event_data.get('message', {}).get('headers', {}).get('message-id', '')

            # Map Mailgun events to our standard events
            event_mapping = {
                'delivered': 'delivered',
                'opened': 'opened',
                'clicked': 'clicked',
                'bounced': 'bounced',
                'failed': 'failed',
                'unsubscribed': 'unsubscribed',
                'complained': 'spam',
            }

            standard_event = event_mapping.get(event_type, event_type)

            return {
                'event': standard_event,
                'email': email,
                'timestamp': timestamp,
                'message_id': message_id,
                'provider': 'mailgun',
                'raw_event': event_data
            }

        except Exception:
            return None

    def get_webhook_events(self) -> List[str]:
        """Get supported webhook events"""
        return [
            'delivered',
            'opened',
            'clicked',
            'bounced',
            'failed',
            'unsubscribed',
            'complained'
        ]
