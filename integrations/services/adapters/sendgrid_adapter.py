"""
SendGrid email provider adapter
"""
import hashlib
import hmac
import base64
from typing import List, Tuple, Optional, Dict
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition
from python_http_client.exceptions import HTTPError

from .base_adapter import BaseEmailAdapter, EmailMessage, EmailResponse


class SendGridAdapter(BaseEmailAdapter):
    """
    SendGrid email provider adapter
    Documentation: https://docs.sendgrid.com/api-reference
    """

    def __init__(self, api_key: str, api_secret: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(api_key, api_secret, config)
        self.client = SendGridAPIClient(api_key=api_key)

    def get_provider_name(self) -> str:
        return "SendGrid"

    def send_email(self, message: EmailMessage) -> EmailResponse:
        """
        Send a single email via SendGrid

        Args:
            message: EmailMessage object

        Returns:
            EmailResponse with result
        """
        try:
            # Create SendGrid Mail object
            from_email = Email(
                message.from_email,
                message.from_name
            )
            to_email = To(message.to_email)
            subject = message.subject
            html_content = Content("text/html", message.body_html)

            mail = Mail(from_email, to_email, subject, html_content)

            # Add plain text version if provided
            if message.body_text:
                mail.add_content(Content("text/plain", message.body_text))

            # Add reply-to if provided
            if message.reply_to:
                mail.reply_to = Email(message.reply_to)

            # Add CC if provided
            if message.cc:
                for cc_email in message.cc:
                    mail.add_cc(Email(cc_email))

            # Add BCC if provided
            if message.bcc:
                for bcc_email in message.bcc:
                    mail.add_bcc(Email(bcc_email))

            # Add custom headers
            if message.headers:
                for key, value in message.headers.items():
                    mail.add_header(key, value)

            # Add tags as categories
            if message.tags:
                for tag in message.tags:
                    mail.add_category(tag)

            # Add custom args (metadata)
            if message.metadata:
                for key, value in message.metadata.items():
                    mail.add_custom_arg(key, str(value))

            # Add attachments if provided
            if message.attachments:
                for attachment_data in message.attachments:
                    attachment = Attachment()
                    attachment.file_content = FileContent(attachment_data.get('content', ''))
                    attachment.file_name = FileName(attachment_data.get('filename', 'file'))
                    attachment.file_type = FileType(attachment_data.get('type', 'application/octet-stream'))
                    attachment.disposition = Disposition(attachment_data.get('disposition', 'attachment'))
                    mail.add_attachment(attachment)

            # Send email
            response = self.client.send(mail)

            # Extract message ID from headers
            message_id = response.headers.get('X-Message-Id', '')

            return EmailResponse(
                success=True,
                message_id=message_id,
                status_code=response.status_code,
                provider_response={'headers': dict(response.headers)}
            )

        except HTTPError as e:
            return self._handle_error(e, "SendGrid HTTP Error")
        except Exception as e:
            return self._handle_error(e, "SendGrid Error")

    def send_bulk(self, messages: List[EmailMessage]) -> List[EmailResponse]:
        """
        Send multiple emails via SendGrid
        SendGrid supports batch sending, but for simplicity we'll send individually
        For production, consider using SendGrid's batch API

        Args:
            messages: List of EmailMessage objects

        Returns:
            List of EmailResponse objects
        """
        responses = []
        for message in messages:
            response = self.send_email(message)
            responses.append(response)
        return responses

    def validate_api_key(self) -> Tuple[bool, str]:
        """
        Validate SendGrid API key by making a test API call

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Test API key with a simple API call
            response = self.client.client.api_keys.get()
            if response.status_code == 200:
                return True, "API key is valid"
            else:
                return False, f"API key validation failed with status {response.status_code}"
        except HTTPError as e:
            if e.status_code == 401 or e.status_code == 403:
                return False, "Invalid API key - Authentication failed"
            return False, f"API key validation error: {str(e)}"
        except Exception as e:
            return False, f"API key validation error: {str(e)}"

    def verify_sender(self, email: str) -> Tuple[bool, str]:
        """
        Verify that the sender email is verified in SendGrid

        Args:
            email: Email address to verify

        Returns:
            Tuple of (is_verified, message)
        """
        try:
            # Check verified senders
            response = self.client.client.verified_senders.get()

            if response.status_code == 200:
                verified_senders = response.to_dict.get('results', [])
                for sender in verified_senders:
                    if sender.get('from_email') == email and sender.get('verified'):
                        return True, "Sender email is verified"

                return False, "Sender email is not verified in SendGrid. Please verify it first."
            else:
                # If we can't check, we'll allow it and let SendGrid handle the validation
                return True, "Unable to verify sender, but proceeding"

        except Exception as e:
            # If verification check fails, we'll allow it and let SendGrid handle it
            return True, f"Unable to verify sender: {str(e)}"

    def get_quota_info(self) -> Optional[Dict]:
        """
        Get quota information from SendGrid

        Returns:
            Dict with quota info
        """
        try:
            # Get stats for current month
            response = self.client.client.stats.get(query_params={'limit': 1})

            if response.status_code == 200:
                stats = response.to_dict
                if stats:
                    latest = stats[0] if isinstance(stats, list) else stats
                    return {
                        'requests': latest.get('stats', [{}])[0].get('metrics', {}).get('requests', 0),
                        'delivered': latest.get('stats', [{}])[0].get('metrics', {}).get('delivered', 0),
                        'bounces': latest.get('stats', [{}])[0].get('metrics', {}).get('bounces', 0),
                    }
            return None
        except Exception:
            return None

    def verify_webhook_signature(self, payload: bytes, signature: str, timestamp: Optional[str] = None) -> bool:
        """
        Verify SendGrid webhook signature

        Args:
            payload: Raw request body
            signature: Signature from X-Twilio-Email-Event-Webhook-Signature header
            timestamp: Timestamp from X-Twilio-Email-Event-Webhook-Timestamp header

        Returns:
            True if signature is valid
        """
        try:
            # SendGrid uses HMAC-SHA256 with a verification key
            # The verification key should be stored in config
            verification_key = self.config.get('webhook_verification_key', '')

            if not verification_key:
                # If no verification key is configured, skip verification
                # In production, this should be required
                return True

            # Construct the payload to sign
            if timestamp:
                signed_payload = timestamp.encode() + payload
            else:
                signed_payload = payload

            # Calculate expected signature
            expected_signature = hmac.new(
                verification_key.encode(),
                signed_payload,
                hashlib.sha256
            ).digest()
            expected_signature_b64 = base64.b64encode(expected_signature).decode()

            # Compare signatures
            return hmac.compare_digest(signature, expected_signature_b64)

        except Exception:
            return False

    def parse_webhook_event(self, payload: Dict) -> Optional[Dict]:
        """
        Parse SendGrid webhook event

        Args:
            payload: Webhook payload (SendGrid sends an array of events)

        Returns:
            Standardized event data
        """
        try:
            # SendGrid sends events as an array
            if isinstance(payload, list) and len(payload) > 0:
                event = payload[0]
            else:
                event = payload

            event_type = event.get('event', '')
            email = event.get('email', '')
            timestamp = event.get('timestamp', '')
            message_id = event.get('sg_message_id', '')

            # Map SendGrid events to our standard events
            event_mapping = {
                'delivered': 'delivered',
                'open': 'opened',
                'click': 'clicked',
                'bounce': 'bounced',
                'dropped': 'failed',
                'deferred': 'failed',
                'spamreport': 'spam',
                'unsubscribe': 'unsubscribed',
            }

            standard_event = event_mapping.get(event_type, event_type)

            return {
                'event': standard_event,
                'email': email,
                'timestamp': timestamp,
                'message_id': message_id,
                'provider': 'sendgrid',
                'raw_event': event
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
            'dropped',
            'deferred',
            'spam',
            'unsubscribed'
        ]
