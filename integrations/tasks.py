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


# Enhanced Email Campaign Tasks

@shared_task
def process_drip_campaigns_task():
    """
    Process all active drip campaigns and send due emails
    Run this task periodically (e.g., every 15 minutes)
    """
    from integrations.models import DripCampaign, DripCampaignEnrollment, Email, EmailTemplate
    from integrations.services.template_engine import TemplateEngine
    from integrations.services.email_provider_service import EmailProviderService
    from django.utils import timezone

    try:
        # Get all enrollments that are due for sending
        now = timezone.now()
        due_enrollments = DripCampaignEnrollment.objects.filter(
            status='active',
            next_send_at__lte=now,
            drip_campaign__is_active=True,
            drip_campaign__status='active'
        ).select_related('drip_campaign', 'current_step', 'contact', 'lead')

        sent_count = 0
        failed_count = 0

        template_engine = TemplateEngine()

        for enrollment in due_enrollments:
            try:
                # Get the current step
                step = enrollment.current_step
                drip = enrollment.drip_campaign

                # Get recipient
                recipient = enrollment.contact if enrollment.contact else enrollment.lead
                if not recipient or not recipient.email:
                    continue

                # Get template
                template = step.template
                subject = step.subject_override or template.subject
                content = step.content_override or template.body_html

                # Render template with recipient data
                recipient_data = {
                    'first_name': getattr(recipient, 'first_name', ''),
                    'last_name': getattr(recipient, 'last_name', ''),
                    'email': recipient.email,
                }

                rendered_content = template_engine.render(
                    content,
                    {},
                    recipient=recipient,
                    campaign=None
                )

                # Create email record
                email_obj = Email.objects.create(
                    account=drip.account,
                    drip_campaign_step=step,
                    from_email=drip.account.name,
                    to_email=recipient.email,
                    subject=subject,
                    body_html=rendered_content,
                    status='queued'
                )

                # Send email
                email_data = {
                    'to_email': recipient.email,
                    'subject': subject,
                    'body_html': rendered_content,
                }

                # Send using default provider strategy
                from integrations.models import EmailProvider
                provider = EmailProvider.objects.filter(
                    account=drip.account,
                    is_active=True
                ).first()

                if provider:
                    response = EmailProviderService.send_email(provider, email_data)

                    if response.success:
                        email_obj.status = 'sent'
                        email_obj.sent_at = timezone.now()
                        email_obj.provider_message_id = response.message_id

                        # Update enrollment
                        enrollment.steps_completed += 1
                        step.sent_count += 1
                        step.save(update_fields=['sent_count'])

                        # Check for branching
                        if step.has_branch and step.branch_conditions:
                            # Simplified branching logic - can be expanded
                            next_step = step.branch_true_step or _get_next_step(step)
                        else:
                            next_step = _get_next_step(step)

                        if next_step:
                            enrollment.current_step = next_step
                            enrollment.next_send_at = _calculate_next_send_time(
                                next_step, drip.skip_weekends, drip.send_time_hour
                            )
                        else:
                            # Sequence completed
                            enrollment.status = 'completed'
                            enrollment.completed_at = timezone.now()

                        enrollment.save()
                        sent_count += 1
                    else:
                        email_obj.status = 'failed'
                        email_obj.error_message = response.error_message
                        failed_count += 1

                    email_obj.save()

            except Exception as e:
                logger.error(f"Error processing drip enrollment {enrollment.id}: {str(e)}", exc_info=True)
                failed_count += 1

        logger.info(f"Drip campaigns processed: {sent_count} sent, {failed_count} failed")

        return {
            'success': True,
            'sent': sent_count,
            'failed': failed_count
        }

    except Exception as e:
        logger.error(f"Error processing drip campaigns: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}


def _get_next_step(current_step):
    """Get the next step in sequence"""
    from integrations.models import DripCampaignStep

    next_step_number = current_step.step_number + 1
    return DripCampaignStep.objects.filter(
        drip_campaign=current_step.drip_campaign,
        step_number=next_step_number,
        is_active=True
    ).first()


def _calculate_next_send_time(step, skip_weekends=False, send_hour=10):
    """Calculate next send time based on step delay"""
    from django.utils import timezone
    import datetime

    now = timezone.now()

    # Add delay based on step settings
    if step.delay_unit == 'minutes':
        next_time = now + timezone.timedelta(minutes=step.delay_value)
    elif step.delay_unit == 'hours':
        next_time = now + timezone.timedelta(hours=step.delay_value)
    elif step.delay_unit == 'days':
        next_time = now + timezone.timedelta(days=step.delay_value)
    elif step.delay_unit == 'weeks':
        next_time = now + timezone.timedelta(weeks=step.delay_value)
    else:
        next_time = now + timezone.timedelta(days=1)

    # Set to specific hour if configured
    if send_hour:
        next_time = next_time.replace(hour=send_hour, minute=0, second=0)

    # Skip weekends if configured
    if skip_weekends:
        while next_time.weekday() >= 5:  # 5=Saturday, 6=Sunday
            next_time += timezone.timedelta(days=1)

    return next_time


@shared_task
def calculate_ab_test_results_task(ab_test_id):
    """
    Calculate A/B test results and determine winner

    Args:
        ab_test_id: CampaignABTest ID
    """
    from integrations.models import CampaignABTest
    from django.utils import timezone
    import math

    try:
        ab_test = CampaignABTest.objects.get(id=ab_test_id)

        # Collect variant data
        variants = []
        for variant in ['a', 'b', 'c', 'd', 'e']:
            sent = getattr(ab_test, f'variant_{variant}_sent', 0)
            if sent > 0:
                opens = getattr(ab_test, f'variant_{variant}_opens', 0)
                clicks = getattr(ab_test, f'variant_{variant}_clicks', 0)
                conversions = getattr(ab_test, f'variant_{variant}_conversions', 0)

                # Calculate rate based on win metric
                if ab_test.win_metric == 'open_rate':
                    rate = opens / sent
                elif ab_test.win_metric == 'click_rate':
                    rate = clicks / sent
                elif ab_test.win_metric == 'conversion_rate':
                    rate = conversions / sent
                else:
                    rate = opens / sent

                variants.append({
                    'name': variant,
                    'sent': sent,
                    'rate': rate,
                    'successes': opens if ab_test.win_metric == 'open_rate' else clicks if ab_test.win_metric == 'click_rate' else conversions
                })

        if len(variants) < 2:
            return {'success': False, 'error': 'Not enough variants'}

        # Find winner (highest rate)
        winner = max(variants, key=lambda x: x['rate'])

        # Simple statistical significance check using z-test for proportions
        # Compare winner with second best
        sorted_variants = sorted(variants, key=lambda x: x['rate'], reverse=True)
        if len(sorted_variants) >= 2:
            v1 = sorted_variants[0]
            v2 = sorted_variants[1]

            # Calculate z-score
            p1 = v1['rate']
            p2 = v2['rate']
            n1 = v1['sent']
            n2 = v2['sent']

            pooled_p = (v1['successes'] + v2['successes']) / (n1 + n2)
            se = math.sqrt(pooled_p * (1 - pooled_p) * (1/n1 + 1/n2))

            if se > 0:
                z_score = abs(p1 - p2) / se
                # For 95% confidence, z-score should be > 1.96
                is_significant = z_score > 1.96
            else:
                is_significant = False
        else:
            is_significant = False

        # Update AB test with results
        ab_test.winner_variant = winner['name']
        ab_test.is_statistically_significant = is_significant
        ab_test.status = 'completed'
        ab_test.completed_at = timezone.now()
        ab_test.save()

        logger.info(f"A/B test {ab_test_id} completed: Winner is variant {winner['name']}")

        return {
            'success': True,
            'winner': winner['name'],
            'is_significant': is_significant
        }

    except CampaignABTest.DoesNotExist:
        logger.error(f"CampaignABTest {ab_test_id} not found")
        return {'success': False, 'error': 'A/B test not found'}
    except Exception as e:
        logger.error(f"Error calculating A/B test results: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}


@shared_task
def update_segment_sizes_task():
    """
    Update cached sizes for all dynamic segments
    Run this task periodically (e.g., hourly)
    """
    from integrations.models import Segment
    from integrations.services.segmentation_engine import SegmentationEngine

    try:
        # Get all active dynamic segments with auto-update enabled
        segments = Segment.objects.filter(
            is_active=True,
            auto_update=True,
            segment_type='dynamic'
        )

        updated_count = 0

        for segment in segments:
            try:
                engine = SegmentationEngine(segment.account)
                engine.update_segment_size(segment)
                updated_count += 1
            except Exception as e:
                logger.error(f"Error updating segment {segment.id}: {str(e)}")

        logger.info(f"Updated {updated_count} segment sizes")

        return {
            'success': True,
            'updated': updated_count
        }

    except Exception as e:
        logger.error(f"Error updating segment sizes: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}


@shared_task
def calculate_campaign_analytics_task(campaign_id):
    """
    Calculate and cache campaign analytics

    Args:
        campaign_id: EmailCampaign ID
    """
    from integrations.models import EmailCampaign, Email, EmailEngagement, LinkClick
    from django.db.models import Count, Q

    try:
        campaign = EmailCampaign.objects.get(id=campaign_id)

        # Calculate engagement metrics
        emails = Email.objects.filter(campaign=campaign)
        total_sent = emails.count()

        if total_sent > 0:
            # Opens
            opened_emails = emails.filter(engagement__opens_count__gt=0).distinct()
            campaign.opens_count = EmailEngagement.objects.filter(
                email__campaign=campaign
            ).aggregate(total=Count('id'))['total'] or 0
            campaign.unique_opens = opened_emails.count()
            campaign.open_rate = (campaign.unique_opens / total_sent) * 100

            # Clicks
            clicked_emails = emails.filter(link_clicks__isnull=False).distinct()
            campaign.clicks_count = LinkClick.objects.filter(
                email__campaign=campaign
            ).count()
            campaign.unique_clicks = clicked_emails.count()
            campaign.click_rate = (campaign.unique_clicks / total_sent) * 100

            # Click-to-open rate
            if campaign.unique_opens > 0:
                campaign.click_to_open_rate = (campaign.unique_clicks / campaign.unique_opens) * 100

            # Bounces
            campaign.bounced_count = emails.filter(status='bounced').count()
            campaign.bounce_rate = (campaign.bounced_count / total_sent) * 100

            # Failed
            campaign.failed_count = emails.filter(status='failed').count()

            campaign.save()

            logger.info(f"Analytics calculated for campaign {campaign_id}")

            return {'success': True, 'campaign_id': campaign_id}

        return {'success': False, 'error': 'No emails sent'}

    except EmailCampaign.DoesNotExist:
        logger.error(f"EmailCampaign {campaign_id} not found")
        return {'success': False, 'error': 'Campaign not found'}
    except Exception as e:
        logger.error(f"Error calculating campaign analytics: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}


@shared_task
def update_campaign_goals_task(campaign_id):
    """
    Update progress for all goals associated with a campaign

    Args:
        campaign_id: EmailCampaign ID
    """
    from integrations.models import CampaignGoal, EmailCampaign
    from django.utils import timezone

    try:
        campaign = EmailCampaign.objects.get(id=campaign_id)
        goals = CampaignGoal.objects.filter(campaign=campaign)

        for goal in goals:
            # Update actual value based on goal type
            if goal.goal_type == 'open_rate':
                goal.actual_value = campaign.open_rate
            elif goal.goal_type == 'click_rate':
                goal.actual_value = campaign.click_rate
            elif goal.goal_type == 'conversion_rate':
                goal.actual_value = campaign.conversion_rate
            elif goal.goal_type == 'total_opens':
                goal.actual_value = campaign.unique_opens
            elif goal.goal_type == 'total_clicks':
                goal.actual_value = campaign.unique_clicks
            elif goal.goal_type == 'total_conversions':
                goal.actual_value = campaign.conversion_count
            elif goal.goal_type == 'revenue':
                goal.actual_value = float(campaign.revenue_generated)

            # Calculate progress
            if goal.target_value > 0:
                goal.progress_percentage = min((goal.actual_value / goal.target_value) * 100, 100)

            # Check if achieved
            if goal.actual_value >= goal.target_value and not goal.is_achieved:
                goal.is_achieved = True
                goal.achieved_at = timezone.now()

            goal.save()

        logger.info(f"Updated {goals.count()} goals for campaign {campaign_id}")

        return {'success': True, 'goals_updated': goals.count()}

    except EmailCampaign.DoesNotExist:
        logger.error(f"EmailCampaign {campaign_id} not found")
        return {'success': False, 'error': 'Campaign not found'}
    except Exception as e:
        logger.error(f"Error updating campaign goals: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}
