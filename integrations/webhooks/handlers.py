"""
Webhook event handlers for email providers
"""
from django.utils import timezone
from django.db import models
from integrations.models import Email, EmailCampaign
import logging

logger = logging.getLogger(__name__)


class EmailWebhookHandler:
    """
    Handle webhook events from email providers
    Updates email status in database
    """

    @staticmethod
    def handle_event(provider_type: str, event_data: dict) -> bool:
        """
        Process webhook event and update email status

        Args:
            provider_type: Provider type (sendgrid, mailgun, etc.)
            event_data: Standardized event data from adapter

        Returns:
            True if handled successfully
        """
        try:
            event = event_data.get('event')
            email_address = event_data.get('email')
            message_id = event_data.get('message_id')
            timestamp = event_data.get('timestamp')

            if not email_address or not event:
                logger.warning(f"Missing required fields in webhook event: {event_data}")
                return False

            # Find the email record
            # Try to find by provider_message_id first, then by tracking_id
            email_obj = None

            if message_id:
                email_obj = Email.objects.filter(provider_message_id=message_id).first()

            if not email_obj and email_address:
                # Fallback: find by email address (most recent)
                email_obj = Email.objects.filter(
                    to_email=email_address,
                    status__in=['queued', 'sent', 'delivered', 'opened', 'clicked']
                ).order_by('-created_at').first()

            if not email_obj:
                logger.warning(f"Email not found for webhook event: {email_address}, {message_id}")
                return False

            # Update email status based on event
            previous_status = email_obj.status
            timestamp_obj = None

            if timestamp:
                try:
                    # Parse timestamp (Unix timestamp)
                    from datetime import datetime
                    if isinstance(timestamp, (int, float)):
                        timestamp_obj = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                    else:
                        timestamp_obj = timezone.now()
                except:
                    timestamp_obj = timezone.now()
            else:
                timestamp_obj = timezone.now()

            # Map events to email status
            if event == 'delivered':
                email_obj.status = 'delivered'
                email_obj.delivered_at = timestamp_obj
                if not email_obj.sent_at:
                    email_obj.sent_at = timestamp_obj

            elif event == 'opened':
                email_obj.status = 'opened'
                email_obj.opened_at = timestamp_obj
                if not email_obj.delivered_at:
                    email_obj.delivered_at = timestamp_obj

                # Update campaign opened count
                if email_obj.campaign:
                    EmailCampaign.objects.filter(id=email_obj.campaign.id).update(
                        opened_count=models.F('opened_count') + 1
                    )

            elif event == 'clicked':
                email_obj.status = 'clicked'
                email_obj.clicked_at = timestamp_obj

                # Update campaign clicked count
                if email_obj.campaign:
                    EmailCampaign.objects.filter(id=email_obj.campaign.id).update(
                        clicked_count=models.F('clicked_count') + 1
                    )

            elif event == 'bounced':
                email_obj.status = 'bounced'
                error_message = event_data.get('raw_event', {}).get('reason', 'Email bounced')
                email_obj.error_message = error_message

                # Update campaign bounced count
                if email_obj.campaign:
                    EmailCampaign.objects.filter(id=email_obj.campaign.id).update(
                        bounced_count=models.F('bounced_count') + 1
                    )

            elif event == 'spam':
                email_obj.status = 'bounced'
                email_obj.error_message = 'Marked as spam'

            elif event == 'failed':
                email_obj.status = 'failed'
                error_message = event_data.get('raw_event', {}).get('reason', 'Email failed')
                email_obj.error_message = error_message

            elif event == 'unsubscribed':
                # Handle unsubscribe (could update contact preferences)
                logger.info(f"Unsubscribe event for {email_address}")
                # TODO: Update contact unsubscribe status

            email_obj.save()

            logger.info(
                f"Updated email {email_obj.id} from {previous_status} to {email_obj.status} "
                f"via {provider_type} webhook"
            )

            return True

        except Exception as e:
            logger.error(f"Error handling webhook event: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def process_bulk_events(provider_type: str, events: list) -> dict:
        """
        Process multiple webhook events

        Args:
            provider_type: Provider type
            events: List of event data dictionaries

        Returns:
            Dictionary with success and failure counts
        """
        success_count = 0
        failure_count = 0

        for event_data in events:
            if EmailWebhookHandler.handle_event(provider_type, event_data):
                success_count += 1
            else:
                failure_count += 1

        return {
            'success_count': success_count,
            'failure_count': failure_count,
            'total': len(events)
        }
