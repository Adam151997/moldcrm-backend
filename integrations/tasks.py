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


# Plugin Integration Tasks

@shared_task(bind=True, max_retries=3)
def sync_plugin_data_task(self, plugin_id, sync_type, **kwargs):
    """
    Sync data from plugin platform asynchronously

    Args:
        plugin_id: Plugin ID
        sync_type: Type of sync (campaigns, leads, orders, etc.)
        **kwargs: Additional sync parameters

    Returns:
        Dictionary with sync result
    """
    from integrations.models import Plugin
    from integrations.plugins.plugin_service import PluginService

    try:
        plugin = Plugin.objects.get(id=plugin_id)

        # Perform sync
        result = PluginService.sync_plugin_data(plugin, sync_type, **kwargs)

        return {
            'success': result.success,
            'records_fetched': result.records_fetched,
            'records_created': result.records_created,
            'records_updated': result.records_updated,
            'error': result.error
        }

    except Plugin.DoesNotExist:
        logger.error(f"Plugin {plugin_id} not found")
        return {'success': False, 'error': 'Plugin not found'}

    except Exception as e:
        logger.error(f"Error syncing plugin data: {str(e)}", exc_info=True)

        # Retry with exponential backoff
        try:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            return {'success': False, 'error': f'Max retries exceeded: {str(e)}'}


@shared_task
def process_plugin_event_task(event_id):
    """
    Process plugin webhook event asynchronously

    Args:
        event_id: PluginEvent ID

    Returns:
        Dictionary with processing result
    """
    from integrations.models import PluginEvent, Lead, Contact, Deal
    from django.utils import timezone

    try:
        event = PluginEvent.objects.get(id=event_id)

        # Mark as processing
        event.status = 'processed'

        # Process based on event type
        if 'lead' in event.event_type.lower():
            # Create or update lead from event data
            lead_data = event.processed_data

            # Extract lead information from platform-specific format
            email = lead_data.get('email') or lead_data.get('field_data', {}).get('email')
            name = lead_data.get('name') or lead_data.get('full_name')

            if email:
                lead, created = Lead.objects.get_or_create(
                    account=event.plugin.account,
                    email=email,
                    defaults={
                        'company': name or 'Unknown',
                        'status': 'new',
                        'source': event.plugin.get_plugin_type_display()
                    }
                )
                event.lead = lead

        elif 'customer' in event.event_type.lower() or 'order' in event.event_type.lower():
            # Create or update contact from customer/order data
            customer_data = event.processed_data

            email = customer_data.get('email')
            first_name = customer_data.get('first_name', '')
            last_name = customer_data.get('last_name', '')

            if email:
                contact, created = Contact.objects.get_or_create(
                    account=event.plugin.account,
                    email=email,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name
                    }
                )
                event.contact = contact

                # If it's an order event, create a deal
                if 'order' in event.event_type.lower():
                    order_value = customer_data.get('total_price') or customer_data.get('amount', 0)

                    deal = Deal.objects.create(
                        account=event.plugin.account,
                        contact=contact,
                        title=f"Order from {event.plugin.name}",
                        amount=float(order_value) if order_value else 0,
                        source=event.plugin.get_plugin_type_display()
                    )
                    event.deal = deal

        event.processed_at = timezone.now()
        event.save()

        logger.info(f"Plugin event {event_id} processed successfully")

        return {'success': True, 'event_id': event_id}

    except PluginEvent.DoesNotExist:
        logger.error(f"PluginEvent {event_id} not found")
        return {'success': False, 'error': 'Event not found'}

    except Exception as e:
        logger.error(f"Error processing plugin event: {str(e)}", exc_info=True)

        try:
            event = PluginEvent.objects.get(id=event_id)
            event.status = 'failed'
            event.error_message = str(e)
            event.save()
        except:
            pass

        return {'success': False, 'error': str(e)}


@shared_task
def refresh_plugin_tokens_task():
    """
    Check and refresh expired plugin tokens
    Run this task periodically via Celery Beat (e.g., hourly)
    """
    from integrations.models import Plugin
    from integrations.plugins.plugin_service import PluginService
    from django.utils import timezone

    try:
        # Get plugins with tokens that are expired or about to expire (within 1 hour)
        soon = timezone.now() + timezone.timedelta(hours=1)
        plugins_to_refresh = Plugin.objects.filter(
            is_active=True,
            status='connected',
            token_expires_at__lte=soon
        )

        refreshed_count = 0
        failed_count = 0

        for plugin in plugins_to_refresh:
            success = PluginService.refresh_token_if_needed(plugin)
            if success:
                refreshed_count += 1
            else:
                failed_count += 1

        logger.info(f"Token refresh completed: {refreshed_count} refreshed, {failed_count} failed")

        return {
            'success': True,
            'refreshed': refreshed_count,
            'failed': failed_count
        }

    except Exception as e:
        logger.error(f"Error refreshing plugin tokens: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}


@shared_task
def scheduled_plugin_sync_task():
    """
    Run scheduled syncs for all active plugins
    Run this task periodically via Celery Beat (e.g., hourly)
    """
    from integrations.models import Plugin
    from integrations.plugins.plugin_service import PluginService
    from django.utils import timezone

    try:
        # Get active plugins that need syncing
        plugins = Plugin.objects.filter(
            is_active=True,
            status='connected'
        )

        synced_count = 0
        failed_count = 0

        for plugin in plugins:
            # Check if sync is due based on sync_frequency
            if plugin.last_sync_at:
                next_sync = plugin.last_sync_at + timezone.timedelta(seconds=plugin.sync_frequency)
                if timezone.now() < next_sync:
                    continue  # Not due yet

            # Determine sync type based on plugin type
            sync_types = {
                'google_ads': ['campaigns'],
                'meta_ads': ['campaigns', 'leads'],
                'tiktok_ads': ['campaigns'],
                'shopify': ['orders', 'customers']
            }

            plugin_sync_types = sync_types.get(plugin.plugin_type, [])

            for sync_type in plugin_sync_types:
                try:
                    result = PluginService.sync_plugin_data(plugin, sync_type)
                    if result.success:
                        synced_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Error syncing {plugin.name} ({sync_type}): {str(e)}")
                    failed_count += 1

        logger.info(f"Scheduled sync completed: {synced_count} successful, {failed_count} failed")

        return {
            'success': True,
            'synced': synced_count,
            'failed': failed_count
        }

    except Exception as e:
        logger.error(f"Error in scheduled plugin sync: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}
