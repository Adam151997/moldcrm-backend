"""
Analytics Service - Comprehensive campaign analytics and reporting
Provides detailed metrics, comparisons, and performance insights
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from django.db.models import Count, Sum, Avg, Max, Min, F, Q, FloatField
from django.db.models.functions import TruncDate, TruncHour, TruncWeek, TruncMonth
from django.utils import timezone
from integrations.models import (
    EmailCampaign, Email, EmailEngagement, LinkClick,
    UnsubscribePreference, CampaignGoal, DripCampaign
)
from crm.models import Contact, Lead


class CampaignAnalyticsService:
    """
    Comprehensive analytics service for email campaigns
    Provides metrics, trends, comparisons, and insights
    """

    def __init__(self, account):
        """
        Initialize analytics service for an account

        Args:
            account: Account instance to scope analytics
        """
        self.account = account

    def get_campaign_overview(self, campaign_id: int) -> Dict[str, Any]:
        """
        Get comprehensive overview of a campaign's performance

        Args:
            campaign_id: EmailCampaign ID

        Returns:
            Dictionary with all campaign metrics
        """
        try:
            campaign = EmailCampaign.objects.get(id=campaign_id, account=self.account)
        except EmailCampaign.DoesNotExist:
            return {}

        # Calculate metrics
        total_sent = campaign.sent_count
        total_delivered = total_sent - campaign.bounced_count
        delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0

        return {
            'campaign_id': campaign.id,
            'campaign_name': campaign.name,
            'status': campaign.status,
            'sent_at': campaign.sent_at,
            'completed_at': campaign.completed_at,

            # Delivery metrics
            'sent_count': total_sent,
            'delivered_count': total_delivered,
            'bounced_count': campaign.bounced_count,
            'failed_count': campaign.failed_count,
            'delivery_rate': round(delivery_rate, 2),
            'bounce_rate': round(campaign.bounce_rate, 2),

            # Engagement metrics
            'opens_count': campaign.opens_count,
            'unique_opens': campaign.unique_opens,
            'clicks_count': campaign.clicks_count,
            'unique_clicks': campaign.unique_clicks,
            'open_rate': round(campaign.open_rate, 2),
            'click_rate': round(campaign.click_rate, 2),
            'click_to_open_rate': round(campaign.click_to_open_rate, 2),

            # Conversion metrics
            'conversion_count': campaign.conversion_count,
            'conversion_rate': round(campaign.conversion_rate, 2),
            'revenue_generated': float(campaign.revenue_generated),
            'average_order_value': float(campaign.average_order_value),

            # Negative metrics
            'unsubscribe_count': campaign.unsubscribe_count,
            'spam_complaint_count': campaign.spam_complaint_count,
            'unsubscribe_rate': round(campaign.unsubscribe_rate, 2),
            'spam_complaint_rate': round(campaign.spam_complaint_rate, 2),

            # Goals progress
            'goals': self._get_campaign_goals(campaign),

            # Device breakdown
            'device_breakdown': self._get_device_breakdown(campaign),

            # Time series data
            'engagement_timeline': self._get_engagement_timeline(campaign),

            # Top links
            'top_links': self._get_top_links(campaign, limit=10),
        }

    def _get_campaign_goals(self, campaign) -> List[Dict[str, Any]]:
        """Get campaign goal progress"""
        goals = CampaignGoal.objects.filter(campaign=campaign)

        return [
            {
                'goal_type': goal.goal_type,
                'target_value': goal.target_value,
                'actual_value': goal.actual_value,
                'progress_percentage': round(goal.progress_percentage, 1),
                'is_achieved': goal.is_achieved,
            }
            for goal in goals
        ]

    def _get_device_breakdown(self, campaign) -> Dict[str, Any]:
        """Get engagement breakdown by device"""
        device_stats = EmailEngagement.objects.filter(
            email__campaign=campaign
        ).values('device_type').annotate(
            count=Count('id'),
            opens=Sum('opens_count'),
            clicks=Sum('clicks_count')
        ).order_by('-count')

        total = sum(stat['count'] for stat in device_stats)

        return {
            'breakdown': [
                {
                    'device': stat['device_type'] or 'Unknown',
                    'count': stat['count'],
                    'percentage': round(stat['count'] / total * 100, 1) if total > 0 else 0,
                    'opens': stat['opens'],
                    'clicks': stat['clicks'],
                }
                for stat in device_stats
            ]
        }

    def _get_engagement_timeline(self, campaign, hours: int = 48) -> List[Dict[str, Any]]:
        """Get engagement timeline (opens/clicks over time)"""
        if not campaign.sent_at:
            return []

        cutoff_time = campaign.sent_at + timedelta(hours=hours)

        # Get hourly engagement data
        timeline = EmailEngagement.objects.filter(
            email__campaign=campaign,
            first_open_at__isnull=False,
            first_open_at__lte=cutoff_time
        ).annotate(
            hour=TruncHour('first_open_at')
        ).values('hour').annotate(
            opens=Count('id', distinct=True),
            clicks=Count('email__link_clicks', distinct=True)
        ).order_by('hour')

        return [
            {
                'timestamp': item['hour'],
                'opens': item['opens'],
                'clicks': item['clicks'],
            }
            for item in timeline
        ]

    def _get_top_links(self, campaign, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most clicked links in campaign"""
        top_links = LinkClick.objects.filter(
            email__campaign=campaign
        ).values('url').annotate(
            clicks=Count('id'),
            unique_clicks=Count('email__recipient_contact', distinct=True)
        ).order_by('-clicks')[:limit]

        return [
            {
                'url': link['url'],
                'clicks': link['clicks'],
                'unique_clicks': link['unique_clicks'],
            }
            for link in top_links
        ]

    def compare_campaigns(self, campaign_ids: List[int]) -> Dict[str, Any]:
        """
        Compare performance of multiple campaigns

        Args:
            campaign_ids: List of campaign IDs to compare

        Returns:
            Dictionary with comparison data
        """
        campaigns = EmailCampaign.objects.filter(
            id__in=campaign_ids,
            account=self.account
        )

        comparison = {
            'campaigns': [],
            'best_performing': {},
            'averages': {}
        }

        metrics_sum = {
            'open_rate': 0,
            'click_rate': 0,
            'conversion_rate': 0,
            'unsubscribe_rate': 0
        }

        best_open_rate = 0
        best_click_rate = 0
        best_conversion_rate = 0

        for campaign in campaigns:
            campaign_data = {
                'id': campaign.id,
                'name': campaign.name,
                'sent_at': campaign.sent_at,
                'sent_count': campaign.sent_count,
                'open_rate': round(campaign.open_rate, 2),
                'click_rate': round(campaign.click_rate, 2),
                'conversion_rate': round(campaign.conversion_rate, 2),
                'unsubscribe_rate': round(campaign.unsubscribe_rate, 2),
                'revenue': float(campaign.revenue_generated),
            }
            comparison['campaigns'].append(campaign_data)

            # Track metrics for averages
            metrics_sum['open_rate'] += campaign.open_rate
            metrics_sum['click_rate'] += campaign.click_rate
            metrics_sum['conversion_rate'] += campaign.conversion_rate
            metrics_sum['unsubscribe_rate'] += campaign.unsubscribe_rate

            # Track best performing
            if campaign.open_rate > best_open_rate:
                best_open_rate = campaign.open_rate
                comparison['best_performing']['open_rate'] = campaign_data

            if campaign.click_rate > best_click_rate:
                best_click_rate = campaign.click_rate
                comparison['best_performing']['click_rate'] = campaign_data

            if campaign.conversion_rate > best_conversion_rate:
                best_conversion_rate = campaign.conversion_rate
                comparison['best_performing']['conversion_rate'] = campaign_data

        # Calculate averages
        count = len(comparison['campaigns'])
        if count > 0:
            comparison['averages'] = {
                'open_rate': round(metrics_sum['open_rate'] / count, 2),
                'click_rate': round(metrics_sum['click_rate'] / count, 2),
                'conversion_rate': round(metrics_sum['conversion_rate'] / count, 2),
                'unsubscribe_rate': round(metrics_sum['unsubscribe_rate'] / count, 2),
            }

        return comparison

    def get_segment_performance(self, segment_id: int, date_range: int = 30) -> Dict[str, Any]:
        """
        Analyze performance of campaigns sent to a specific segment

        Args:
            segment_id: Segment ID
            date_range: Number of days to analyze

        Returns:
            Dictionary with segment performance data
        """
        cutoff_date = timezone.now() - timedelta(days=date_range)

        campaigns = EmailCampaign.objects.filter(
            segment_id=segment_id,
            account=self.account,
            sent_at__gte=cutoff_date
        )

        if not campaigns.exists():
            return {}

        # Aggregate metrics
        total_campaigns = campaigns.count()
        avg_open_rate = campaigns.aggregate(avg=Avg('open_rate'))['avg'] or 0
        avg_click_rate = campaigns.aggregate(avg=Avg('click_rate'))['avg'] or 0
        avg_conversion_rate = campaigns.aggregate(avg=Avg('conversion_rate'))['avg'] or 0
        total_revenue = campaigns.aggregate(total=Sum('revenue_generated'))['total'] or 0

        return {
            'segment_id': segment_id,
            'total_campaigns': total_campaigns,
            'date_range_days': date_range,
            'metrics': {
                'average_open_rate': round(avg_open_rate, 2),
                'average_click_rate': round(avg_click_rate, 2),
                'average_conversion_rate': round(avg_conversion_rate, 2),
                'total_revenue': float(total_revenue),
            },
            'campaigns': [
                {
                    'id': c.id,
                    'name': c.name,
                    'sent_at': c.sent_at,
                    'open_rate': round(c.open_rate, 2),
                }
                for c in campaigns.order_by('-sent_at')[:10]
            ]
        }

    def get_drip_campaign_analytics(self, drip_campaign_id: int) -> Dict[str, Any]:
        """
        Get analytics for a drip campaign

        Args:
            drip_campaign_id: DripCampaign ID

        Returns:
            Dictionary with drip campaign analytics
        """
        from integrations.models import DripCampaign, DripCampaignStep, DripCampaignEnrollment

        try:
            drip = DripCampaign.objects.get(id=drip_campaign_id, account=self.account)
        except DripCampaign.DoesNotExist:
            return {}

        enrollments = DripCampaignEnrollment.objects.filter(drip_campaign=drip)
        total_enrolled = enrollments.count()
        active_enrolled = enrollments.filter(status='active').count()
        completed = enrollments.filter(status='completed').count()
        paused = enrollments.filter(status='paused').count()

        # Step performance
        steps = DripCampaignStep.objects.filter(drip_campaign=drip).order_by('step_number')
        step_performance = []

        for step in steps:
            # Get emails sent for this step
            step_emails = Email.objects.filter(
                drip_campaign_step=step
            )

            if step_emails.exists():
                step_stats = step_emails.aggregate(
                    sent=Count('id'),
                    opened=Count('id', filter=Q(engagement__opens_count__gt=0)),
                    clicked=Count('id', filter=Q(link_clicks__isnull=False))
                )

                open_rate = (step_stats['opened'] / step_stats['sent'] * 100) if step_stats['sent'] > 0 else 0
                click_rate = (step_stats['clicked'] / step_stats['sent'] * 100) if step_stats['sent'] > 0 else 0

                step_performance.append({
                    'step_number': step.step_number,
                    'delay': f"{step.delay_value} {step.delay_unit}",
                    'sent_count': step_stats['sent'],
                    'open_rate': round(open_rate, 2),
                    'click_rate': round(click_rate, 2),
                })

        return {
            'drip_campaign_id': drip.id,
            'name': drip.name,
            'status': drip.status,
            'enrollments': {
                'total': total_enrolled,
                'active': active_enrolled,
                'completed': completed,
                'paused': paused,
            },
            'step_performance': step_performance,
            'completion_rate': round((completed / total_enrolled * 100) if total_enrolled > 0 else 0, 2),
        }

    def get_email_provider_performance(self, date_range: int = 30) -> List[Dict[str, Any]]:
        """
        Compare performance across email providers

        Args:
            date_range: Number of days to analyze

        Returns:
            List of provider performance data
        """
        from integrations.models import EmailProvider

        cutoff_date = timezone.now() - timedelta(days=date_range)

        providers = EmailProvider.objects.filter(
            account=self.account,
            is_active=True
        )

        performance = []

        for provider in providers:
            # Get campaigns sent via this provider
            campaigns = EmailCampaign.objects.filter(
                account=self.account,
                email_provider=provider,
                sent_at__gte=cutoff_date
            )

            if campaigns.exists():
                stats = campaigns.aggregate(
                    total_sent=Sum('sent_count'),
                    total_delivered=Sum('sent_count') - Sum('bounced_count'),
                    avg_open_rate=Avg('open_rate'),
                    avg_click_rate=Avg('click_rate'),
                    avg_bounce_rate=Avg('bounce_rate'),
                )

                performance.append({
                    'provider_name': provider.provider_name,
                    'total_campaigns': campaigns.count(),
                    'total_sent': stats['total_sent'] or 0,
                    'total_delivered': stats['total_delivered'] or 0,
                    'average_open_rate': round(stats['avg_open_rate'] or 0, 2),
                    'average_click_rate': round(stats['avg_click_rate'] or 0, 2),
                    'average_bounce_rate': round(stats['avg_bounce_rate'] or 0, 2),
                })

        return sorted(performance, key=lambda x: x['average_open_rate'], reverse=True)

    def get_contact_engagement_history(self, contact_id: int, limit: int = 50) -> Dict[str, Any]:
        """
        Get detailed engagement history for a contact

        Args:
            contact_id: Contact ID
            limit: Maximum number of emails to return

        Returns:
            Dictionary with contact's email engagement history
        """
        try:
            contact = Contact.objects.get(id=contact_id, account=self.account)
        except Contact.DoesNotExist:
            return {}

        emails = Email.objects.filter(
            recipient_contact=contact
        ).select_related('campaign', 'engagement').order_by('-sent_at')[:limit]

        engagement_history = []
        total_sent = 0
        total_opened = 0
        total_clicked = 0

        for email in emails:
            engagement = getattr(email, 'engagement', None)

            opened = engagement and engagement.opens_count > 0
            clicked = LinkClick.objects.filter(email=email).exists()

            total_sent += 1
            if opened:
                total_opened += 1
            if clicked:
                total_clicked += 1

            engagement_history.append({
                'email_id': email.id,
                'campaign_name': email.campaign.name if email.campaign else 'N/A',
                'subject': email.subject,
                'sent_at': email.sent_at,
                'opened': opened,
                'opened_at': engagement.first_open_at if engagement else None,
                'opens_count': engagement.opens_count if engagement else 0,
                'clicked': clicked,
                'clicks_count': LinkClick.objects.filter(email=email).count(),
                'status': email.status,
            })

        # Calculate overall metrics
        open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
        click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0

        # Calculate engagement score
        from integrations.services.email_ai_service import EmailAIService
        ai_service = EmailAIService()
        engagement_score = ai_service.calculate_engagement_score([
            {'opened': e['opened'], 'clicked': e['clicked']}
            for e in engagement_history
        ])

        return {
            'contact_id': contact.id,
            'contact_name': contact.get_full_name(),
            'email': contact.email,
            'overall_metrics': {
                'total_emails_received': total_sent,
                'total_opened': total_opened,
                'total_clicked': total_clicked,
                'open_rate': round(open_rate, 2),
                'click_rate': round(click_rate, 2),
                'engagement_score': engagement_score,
            },
            'engagement_history': engagement_history,
        }

    def get_revenue_attribution(self, date_range: int = 30) -> Dict[str, Any]:
        """
        Get revenue attribution by campaign

        Args:
            date_range: Number of days to analyze

        Returns:
            Dictionary with revenue attribution data
        """
        cutoff_date = timezone.now() - timedelta(days=date_range)

        campaigns = EmailCampaign.objects.filter(
            account=self.account,
            sent_at__gte=cutoff_date,
            revenue_generated__gt=0
        ).order_by('-revenue_generated')

        total_revenue = campaigns.aggregate(total=Sum('revenue_generated'))['total'] or 0

        attribution = []
        for campaign in campaigns:
            revenue = float(campaign.revenue_generated)
            attribution.append({
                'campaign_id': campaign.id,
                'campaign_name': campaign.name,
                'revenue': revenue,
                'percentage': round((revenue / total_revenue * 100) if total_revenue > 0 else 0, 2),
                'conversions': campaign.conversion_count,
                'average_order_value': float(campaign.average_order_value),
                'roi': self._calculate_roi(campaign),
            })

        return {
            'date_range_days': date_range,
            'total_revenue': float(total_revenue),
            'attribution': attribution,
        }

    def _calculate_roi(self, campaign) -> float:
        """Calculate ROI for a campaign"""
        # Simplified ROI calculation
        # In production, you'd factor in actual campaign costs
        revenue = float(campaign.revenue_generated)
        estimated_cost = campaign.sent_count * 0.01  # Assume $0.01 per email

        if estimated_cost == 0:
            return 0.0

        roi = ((revenue - estimated_cost) / estimated_cost) * 100
        return round(roi, 2)

    def get_global_stats(self, date_range: int = 30) -> Dict[str, Any]:
        """
        Get global statistics for the account

        Args:
            date_range: Number of days to analyze

        Returns:
            Dictionary with account-wide statistics
        """
        cutoff_date = timezone.now() - timedelta(days=date_range)

        campaigns = EmailCampaign.objects.filter(
            account=self.account,
            sent_at__gte=cutoff_date
        )

        stats = campaigns.aggregate(
            total_campaigns=Count('id'),
            total_sent=Sum('sent_count'),
            total_delivered=Sum('sent_count') - Sum('bounced_count'),
            total_opens=Sum('opens_count'),
            total_clicks=Sum('clicks_count'),
            total_conversions=Sum('conversion_count'),
            total_revenue=Sum('revenue_generated'),
            avg_open_rate=Avg('open_rate'),
            avg_click_rate=Avg('click_rate'),
            avg_conversion_rate=Avg('conversion_rate'),
        )

        return {
            'date_range_days': date_range,
            'total_campaigns': stats['total_campaigns'] or 0,
            'total_sent': stats['total_sent'] or 0,
            'total_delivered': stats['total_delivered'] or 0,
            'total_opens': stats['total_opens'] or 0,
            'total_clicks': stats['total_clicks'] or 0,
            'total_conversions': stats['total_conversions'] or 0,
            'total_revenue': float(stats['total_revenue'] or 0),
            'average_open_rate': round(stats['avg_open_rate'] or 0, 2),
            'average_click_rate': round(stats['avg_click_rate'] or 0, 2),
            'average_conversion_rate': round(stats['avg_conversion_rate'] or 0, 2),
        }
