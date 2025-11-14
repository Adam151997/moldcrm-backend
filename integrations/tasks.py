"""
Celery tasks for email sending and provider management
"""
from celery import shared_task
from django.utils import timezone
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_email_task(self, provider_id, email_data):
    """
    Send a single email asynchronously

    Args:
        provider_id: EmailProvider ID
        email_data: Dictionary with email details

    Returns:
        Dictionary with result
    """
    from integrations.models import EmailProvider, Email
    from integrations.services.email_provider_service import EmailProviderService

    try:
        provider = EmailProvider.objects.get(id=provider_id)

        # Send email
        response = EmailProviderService.send_email(provider, email_data)

        return {
            'success': response.success,
            'message_id': response.message_id,
            'error': response.error_message
        }

    except EmailProvider.DoesNotExist:
        logger.error(f"EmailProvider {provider_id} not found")
        return {'success': False, 'error': 'Provider not found'}

    except Exception as e:
        logger.error(f"Error sending email: {str(e)}", exc_info=True)

        # Retry with exponential backoff
        try:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            return {'success': False, 'error': f'Max retries exceeded: {str(e)}'}


@shared_task
def send_campaign_emails_task(campaign_id):
    """
    Send all emails for a campaign asynchronously

    Args:
        campaign_id: EmailCampaign ID

    Returns:
        Dictionary with results
    """
    from integrations.models import EmailCampaign, Email
    from integrations.services.email_provider_service import EmailProviderService
    from crm.models import Contact, Lead

    try:
        campaign = EmailCampaign.objects.get(id=campaign_id)

        # Update campaign status
        campaign.status = 'sending'
        campaign.save(update_fields=['status'])

        # Get recipients based on recipient_filter
        recipient_filter = campaign.recipient_filter or {}

        # Get contacts or leads based on filter
        # This is a simplified version - expand based on your filtering needs
        recipients = []

        if recipient_filter.get('type') == 'contacts':
            contacts = Contact.objects.filter(account=campaign.account)
            recipients = [{'email': c.email, 'name': f"{c.first_name} {c.last_name}"} for c in contacts if c.email]

        elif recipient_filter.get('type') == 'leads':
            leads = Lead.objects.filter(account=campaign.account)
            recipients = [{'email': l.email, 'name': l.company} for l in leads if l.email]

        else:
            # Default: all contacts and leads
            contacts = Contact.objects.filter(account=campaign.account)
            leads = Lead.objects.filter(account=campaign.account)
            recipients = (
                [{'email': c.email, 'name': f"{c.first_name} {c.last_name}"} for c in contacts if c.email] +
                [{'email': l.email, 'name': l.company} for l in leads if l.email]
            )

        # Update total recipients
        campaign.total_recipients = len(recipients)
        campaign.save(update_fields=['total_recipients'])

        # Send emails
        success_count = 0
        failed_count = 0

        for recipient in recipients:
            # Create email record
            email_obj = Email.objects.create(
                account=campaign.account,
                campaign=campaign,
                from_email=campaign.template.name if campaign.template else campaign.account.name,
                to_email=recipient['email'],
                subject=campaign.template.subject if campaign.template else '',
                body_html=campaign.template.body_html if campaign.template else '',
                body_text=campaign.template.body_text if campaign.template else '',
                status='queued'
            )

            # Prepare email data
            email_data = {
                'to_email': recipient['email'],
                'subject': campaign.template.subject if campaign.template else '',
                'body_html': campaign.template.body_html if campaign.template else '',
                'body_text': campaign.template.body_text if campaign.template else '',
            }

            # Send using campaign strategy
            response = EmailProviderService.send_with_strategy(campaign, email_data)

            if response.success:
                email_obj.status = 'sent'
                email_obj.sent_at = timezone.now()
                email_obj.provider_message_id = response.message_id
                success_count += 1
            else:
                email_obj.status = 'failed'
                email_obj.error_message = response.error_message
                failed_count += 1

            email_obj.save()

        # Update campaign status
        campaign.status = 'completed'
        campaign.sent_count = success_count
        campaign.save(update_fields=['status', 'sent_count'])

        logger.info(f"Campaign {campaign_id} completed: {success_count} sent, {failed_count} failed")

        return {
            'success': True,
            'sent': success_count,
            'failed': failed_count,
            'total': len(recipients)
        }

    except EmailCampaign.DoesNotExist:
        logger.error(f"EmailCampaign {campaign_id} not found")
        return {'success': False, 'error': 'Campaign not found'}

    except Exception as e:
        logger.error(f"Error sending campaign: {str(e)}", exc_info=True)

        # Update campaign status to failed
        try:
            campaign = EmailCampaign.objects.get(id=campaign_id)
            campaign.status = 'paused'
            campaign.save(update_fields=['status'])
        except:
            pass

        return {'success': False, 'error': str(e)}


@shared_task
def reset_provider_daily_counters():
    """
    Reset daily sent counters for all providers
    Run this task daily via Celery Beat
    """
    from integrations.services.email_provider_service import EmailProviderService

    try:
        EmailProviderService.reset_daily_counters()
        logger.info("Daily provider counters reset successfully")
        return {'success': True, 'message': 'Daily counters reset'}

    except Exception as e:
        logger.error(f"Error resetting daily counters: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}


@shared_task
def reset_provider_monthly_counters():
    """
    Reset monthly sent counters for all providers
    Run this task monthly via Celery Beat
    """
    from integrations.services.email_provider_service import EmailProviderService

    try:
        EmailProviderService.reset_monthly_counters()
        logger.info("Monthly provider counters reset successfully")
        return {'success': True, 'message': 'Monthly counters reset'}

    except Exception as e:
        logger.error(f"Error resetting monthly counters: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}


@shared_task
def validate_provider_task(provider_id):
    """
    Validate a provider's configuration asynchronously

    Args:
        provider_id: EmailProvider ID

    Returns:
        Dictionary with validation result
    """
    from integrations.models import EmailProvider
    from integrations.services.email_provider_service import EmailProviderService

    try:
        provider = EmailProvider.objects.get(id=provider_id)

        is_valid, message = EmailProviderService.validate_provider(provider)

        if is_valid:
            provider.is_verified = True
            provider.save(update_fields=['is_verified'])

        return {
            'success': is_valid,
            'message': message
        }

    except EmailProvider.DoesNotExist:
        logger.error(f"EmailProvider {provider_id} not found")
        return {'success': False, 'error': 'Provider not found'}

    except Exception as e:
        logger.error(f"Error validating provider: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}
