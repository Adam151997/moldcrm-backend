"""
Brevo (Sendinblue) email provider adapter
"""
from typing import List, Tuple, Optional, Dict
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from .base_adapter import BaseEmailAdapter, EmailMessage, EmailResponse


class BrevoAdapter(BaseEmailAdapter):
    """
    Brevo (formerly Sendinblue) email provider adapter
    Documentation: https://developers.brevo.com/
    """

    def __init__(self, api_key: str, api_secret: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(api_key, api_secret, config)

        # Configure API client
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = api_key
        self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
        self.account_api = sib_api_v3_sdk.AccountApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

    def get_provider_name(self) -> str:
        return "Brevo"

    def send_email(self, message: EmailMessage) -> EmailResponse:
        """
        Send a single email via Brevo

        Args:
            message: EmailMessage object

        Returns:
            EmailResponse with result
        """
        try:
            # Create sender
            sender = {
                "email": message.from_email,
                "name": message.from_name or message.from_email
            }

            # Create recipient
            to = [{"email": message.to_email}]

            # Add CC if provided
            cc_list = None
            if message.cc:
                cc_list = [{"email": email} for email in message.cc]

            # Add BCC if provided
            bcc_list = None
            if message.bcc:
                bcc_list = [{"email": email} for email in message.bcc]

            # Create email object
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                sender=sender,
                to=to,
                subject=message.subject,
                html_content=message.body_html,
                text_content=message.body_text if message.body_text else None,
                cc=cc_list,
                bcc=bcc_list,
                reply_to={"email": message.reply_to} if message.reply_to else None,
                headers=message.headers if message.headers else None,
                tags=message.tags if message.tags else None,
                params=message.metadata if message.metadata else None
            )

            # Send email
            api_response = self.api_instance.send_transac_email(send_smtp_email)

            # Extract message ID
            message_id = api_response.message_id if hasattr(api_response, 'message_id') else ''

            return EmailResponse(
                success=True,
                message_id=message_id,
                status_code=201,
                provider_response={'message_id': message_id}
            )

        except ApiException as e:
            error_message = f"Brevo API Error: {e.status} - {e.reason}"
            if e.body:
                error_message += f" - {e.body}"
            return EmailResponse(
                success=False,
                error_message=error_message,
                status_code=e.status
            )
        except Exception as e:
            return self._handle_error(e, "Brevo Error")

    def send_bulk(self, messages: List[EmailMessage]) -> List[EmailResponse]:
        """
        Send multiple emails via Brevo

        Args:
            messages: List of EmailMessage objects

        Returns:
            List of EmailResponse objects
        """
        responses = []

        # Brevo supports batch sending, but for simplicity send individually
        for message in messages:
            response = self.send_email(message)
            responses.append(response)

        return responses

    def validate_api_key(self) -> Tuple[bool, str]:
        """
        Validate Brevo API key by making a test API call

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Test API key by getting account info
            account_info = self.account_api.get_account()

            if account_info:
                return True, "API key is valid"
            else:
                return False, "Unable to verify API key"

        except ApiException as e:
            if e.status == 401:
                return False, "Invalid API key - Authentication failed"
            return False, f"API key validation error: {e.reason}"
        except Exception as e:
            return False, f"API key validation error: {str(e)}"

    def verify_sender(self, email: str) -> Tuple[bool, str]:
        """
        Verify that the sender email is verified in Brevo

        Args:
            email: Email address to verify

        Returns:
            Tuple of (is_verified, message)
        """
        try:
            # Get list of senders
            senders_api = sib_api_v3_sdk.SendersApi(
                sib_api_v3_sdk.ApiClient(
                    sib_api_v3_sdk.Configuration()
                )
            )
            senders_api.api_client.configuration.api_key['api-key'] = self.api_key

            senders = senders_api.get_senders()

            if senders and hasattr(senders, 'senders'):
                for sender in senders.senders:
                    if sender.email == email and sender.active:
                        return True, "Sender email is verified and active"

                return False, f"Sender email '{email}' is not verified in Brevo"
            else:
                # If we can't check, allow it
                return True, "Unable to verify sender, proceeding"

        except Exception as e:
            # If verification fails, allow it and let Brevo handle it
            return True, f"Unable to verify sender: {str(e)}"

    def get_quota_info(self) -> Optional[Dict]:
        """
        Get quota information from Brevo

        Returns:
            Dict with quota info
        """
        try:
            # Get account info which includes quota
            account_info = self.account_api.get_account()

            if account_info and hasattr(account_info, 'plan'):
                plan = account_info.plan[0] if isinstance(account_info.plan, list) else account_info.plan
                return {
                    'credits': plan.credits if hasattr(plan, 'credits') else 0,
                    'credits_used': plan.credits_used if hasattr(plan, 'credits_used') else 0,
                }
            return None

        except Exception:
            return None

    def verify_webhook_signature(self, payload: bytes, signature: str, timestamp: Optional[str] = None) -> bool:
        """
        Verify Brevo webhook signature

        Args:
            payload: Raw request body
            signature: Signature from headers
            timestamp: Optional timestamp

        Returns:
            True if signature is valid
        """
        # Brevo doesn't provide webhook signature verification
        # You should whitelist Brevo's IP addresses instead
        return True

    def parse_webhook_event(self, payload: Dict) -> Optional[Dict]:
        """
        Parse Brevo webhook event

        Args:
            payload: Webhook payload

        Returns:
            Standardized event data
        """
        try:
            event_type = payload.get('event', '')
            email = payload.get('email', '')
            timestamp = payload.get('date', '')
            message_id = payload.get('message-id', '')

            # Map Brevo events to our standard events
            event_mapping = {
                'delivered': 'delivered',
                'hard_bounce': 'bounced',
                'soft_bounce': 'bounced',
                'blocked': 'failed',
                'spam': 'spam',
                'invalid_email': 'failed',
                'deferred': 'failed',
                'click': 'clicked',
                'opened': 'opened',
                'unique_opened': 'opened',
                'unsubscribed': 'unsubscribed',
            }

            standard_event = event_mapping.get(event_type, event_type)

            return {
                'event': standard_event,
                'email': email,
                'timestamp': timestamp,
                'message_id': message_id,
                'provider': 'brevo',
                'raw_event': payload
            }

        except Exception:
            return None

    def get_webhook_events(self) -> List[str]:
        """Get supported webhook events"""
        return [
            'delivered',
            'hard_bounce',
            'soft_bounce',
            'blocked',
            'spam',
            'invalid_email',
            'deferred',
            'click',
            'opened',
            'unique_opened',
            'unsubscribed'
        ]
