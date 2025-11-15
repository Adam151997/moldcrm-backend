"""
Enhanced Email Campaign ViewSets
Handles segments, drip campaigns, A/B testing, analytics, and AI features
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.shortcuts import get_object_or_404

from integrations.models import (
    Segment, CampaignABTest, DripCampaign, DripCampaignStep, DripCampaignEnrollment,
    EmailEngagement, LinkClick, UnsubscribePreference, CampaignGoal,
    EmailCampaign, EmailTemplate
)
from crm.models import Contact, Lead
from .serializers import (
    SegmentSerializer, CampaignABTestSerializer, DripCampaignSerializer,
    DripCampaignStepSerializer, DripCampaignEnrollmentSerializer,
    EmailEngagementSerializer, LinkClickSerializer, UnsubscribePreferenceSerializer,
    CampaignGoalSerializer
)
from integrations.services.segmentation_engine import SegmentationEngine
from integrations.services.email_ai_service import EmailAIService
from integrations.services.analytics_service import CampaignAnalyticsService
from integrations.services.template_engine import TemplateEngine


class SegmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing audience segments
    Supports dynamic filtering and static segments
    """
    serializer_class = SegmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Segment.objects.filter(account=self.request.user.account).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(account=self.request.user.account, created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """Preview segment members"""
        segment = self.get_object()
        engine = SegmentationEngine(request.user.account)

        preview = engine.preview_segment(
            segment.filter_conditions,
            model_type='contact',
            limit=request.query_params.get('limit', 10)
        )

        return Response({
            'segment_id': segment.id,
            'segment_name': segment.name,
            'preview': preview
        })

    @action(detail=True, methods=['post'])
    def calculate_size(self, request, pk=None):
        """Calculate and update segment size"""
        segment = self.get_object()
        engine = SegmentationEngine(request.user.account)

        new_size = engine.update_segment_size(segment)

        return Response({
            'segment_id': segment.id,
            'actual_size': new_size,
            'estimated_size': segment.estimated_size
        })

    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get performance analytics for campaigns sent to this segment"""
        segment = self.get_object()
        analytics = CampaignAnalyticsService(request.user.account)

        date_range = int(request.query_params.get('days', 30))
        performance = analytics.get_segment_performance(segment.id, date_range)

        return Response(performance)

    @action(detail=False, methods=['post'])
    def validate_conditions(self, request):
        """Validate segment filter conditions"""
        conditions = request.data.get('filter_conditions', {})
        engine = SegmentationEngine(request.user.account)

        try:
            # Try to build queryset to validate conditions
            queryset = engine.build_queryset(conditions, model_type='contact')
            count = queryset.count()

            return Response({
                'valid': True,
                'estimated_size': count
            })
        except Exception as e:
            return Response({
                'valid': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CampaignABTestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing A/B tests
    Supports up to 5 variants per test
    """
    serializer_class = CampaignABTestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CampaignABTest.objects.filter(
            campaign__account=self.request.user.account
        ).order_by('-created_at')

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get detailed A/B test results with statistical analysis"""
        ab_test = self.get_object()

        # Calculate rates for each variant
        variants_data = []
        for variant in ['a', 'b', 'c', 'd', 'e']:
            sent = getattr(ab_test, f'variant_{variant}_sent', 0)
            if sent > 0:
                opens = getattr(ab_test, f'variant_{variant}_opens', 0)
                clicks = getattr(ab_test, f'variant_{variant}_clicks', 0)
                conversions = getattr(ab_test, f'variant_{variant}_conversions', 0)

                variants_data.append({
                    'variant': variant.upper(),
                    'value': getattr(ab_test, f'variant_{variant}_value', ''),
                    'sent': sent,
                    'opens': opens,
                    'clicks': clicks,
                    'conversions': conversions,
                    'open_rate': round((opens / sent * 100) if sent > 0 else 0, 2),
                    'click_rate': round((clicks / sent * 100) if sent > 0 else 0, 2),
                    'conversion_rate': round((conversions / sent * 100) if sent > 0 else 0, 2),
                })

        return Response({
            'test_id': ab_test.id,
            'test_element': ab_test.test_element,
            'win_metric': ab_test.win_metric,
            'winner': ab_test.winner_variant,
            'status': ab_test.status,
            'is_statistically_significant': ab_test.is_statistically_significant,
            'variants': variants_data,
            'started_at': ab_test.started_at,
            'completed_at': ab_test.completed_at,
        })

    @action(detail=True, methods=['post'])
    def select_winner(self, request, pk=None):
        """Manually select the winning variant"""
        ab_test = self.get_object()
        winner_variant = request.data.get('winner_variant')

        if winner_variant not in ['a', 'b', 'c', 'd', 'e']:
            return Response(
                {'error': 'Invalid variant'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ab_test.winner_variant = winner_variant
        ab_test.status = 'completed'
        ab_test.completed_at = timezone.now()
        ab_test.save()

        return Response({
            'message': f'Variant {winner_variant.upper()} selected as winner',
            'winner_variant': winner_variant
        })


class DripCampaignViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing drip campaigns
    Automated email sequences with triggers and branches
    """
    serializer_class = DripCampaignSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DripCampaign.objects.filter(
            account=self.request.user.account
        ).prefetch_related('steps').order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(account=self.request.user.account, created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a drip campaign"""
        drip = self.get_object()
        drip.status = 'active'
        drip.is_active = True
        drip.save()

        return Response({'message': 'Drip campaign activated'})

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause a drip campaign"""
        drip = self.get_object()
        drip.status = 'paused'
        drip.is_active = False
        drip.save()

        return Response({'message': 'Drip campaign paused'})

    @action(detail=True, methods=['post'])
    def enroll_contact(self, request, pk=None):
        """Enroll a contact in the drip campaign"""
        drip = self.get_object()
        contact_id = request.data.get('contact_id')
        lead_id = request.data.get('lead_id')

        if not contact_id and not lead_id:
            return Response(
                {'error': 'Either contact_id or lead_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get first step
        first_step = drip.steps.filter(step_number=1).first()
        if not first_step:
            return Response(
                {'error': 'No steps defined for this drip campaign'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create enrollment
        enrollment_data = {
            'drip_campaign': drip,
            'current_step': first_step,
            'status': 'active',
            'next_send_at': timezone.now() + timezone.timedelta(
                **{f'{first_step.delay_unit}s': first_step.delay_value}
            )
        }

        if contact_id:
            contact = get_object_or_404(Contact, id=contact_id, account=request.user.account)
            enrollment_data['contact'] = contact
        else:
            lead = get_object_or_404(Lead, id=lead_id, account=request.user.account)
            enrollment_data['lead'] = lead

        enrollment = DripCampaignEnrollment.objects.create(**enrollment_data)

        return Response({
            'message': 'Enrolled successfully',
            'enrollment_id': enrollment.id
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get drip campaign analytics"""
        drip = self.get_object()
        analytics = CampaignAnalyticsService(request.user.account)

        analytics_data = analytics.get_drip_campaign_analytics(drip.id)

        return Response(analytics_data)

    @action(detail=True, methods=['get'])
    def enrollments(self, request, pk=None):
        """Get all enrollments for this drip campaign"""
        drip = self.get_object()

        enrollments = DripCampaignEnrollment.objects.filter(
            drip_campaign=drip
        ).select_related('contact', 'lead', 'current_step').order_by('-enrolled_at')

        page = self.paginate_queryset(enrollments)
        if page is not None:
            serializer = DripCampaignEnrollmentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = DripCampaignEnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)


class DripCampaignStepViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing drip campaign steps
    """
    serializer_class = DripCampaignStepSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DripCampaignStep.objects.filter(
            drip_campaign__account=self.request.user.account
        ).order_by('drip_campaign', 'step_number')

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """Reorder steps in a drip campaign"""
        step_ids = request.data.get('step_ids', [])

        for index, step_id in enumerate(step_ids, start=1):
            DripCampaignStep.objects.filter(id=step_id).update(step_number=index)

        return Response({'message': 'Steps reordered successfully'})


class AnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for comprehensive email campaign analytics
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def campaign_overview(self, request):
        """Get overview of a specific campaign"""
        campaign_id = request.query_params.get('campaign_id')
        if not campaign_id:
            return Response(
                {'error': 'campaign_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        analytics = CampaignAnalyticsService(request.user.account)
        overview = analytics.get_campaign_overview(int(campaign_id))

        return Response(overview)

    @action(detail=False, methods=['post'])
    def compare_campaigns(self, request):
        """Compare performance of multiple campaigns"""
        campaign_ids = request.data.get('campaign_ids', [])

        if not campaign_ids or len(campaign_ids) < 2:
            return Response(
                {'error': 'At least 2 campaign IDs are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        analytics = CampaignAnalyticsService(request.user.account)
        comparison = analytics.compare_campaigns(campaign_ids)

        return Response(comparison)

    @action(detail=False, methods=['get'])
    def global_stats(self, request):
        """Get global statistics for the account"""
        days = int(request.query_params.get('days', 30))

        analytics = CampaignAnalyticsService(request.user.account)
        stats = analytics.get_global_stats(date_range=days)

        return Response(stats)

    @action(detail=False, methods=['get'])
    def contact_engagement(self, request):
        """Get engagement history for a contact"""
        contact_id = request.query_params.get('contact_id')
        if not contact_id:
            return Response(
                {'error': 'contact_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        analytics = CampaignAnalyticsService(request.user.account)
        limit = int(request.query_params.get('limit', 50))
        history = analytics.get_contact_engagement_history(int(contact_id), limit)

        return Response(history)

    @action(detail=False, methods=['get'])
    def revenue_attribution(self, request):
        """Get revenue attribution by campaign"""
        days = int(request.query_params.get('days', 30))

        analytics = CampaignAnalyticsService(request.user.account)
        attribution = analytics.get_revenue_attribution(date_range=days)

        return Response(attribution)

    @action(detail=False, methods=['get'])
    def provider_performance(self, request):
        """Compare performance across email providers"""
        days = int(request.query_params.get('days', 30))

        analytics = CampaignAnalyticsService(request.user.account)
        performance = analytics.get_email_provider_performance(date_range=days)

        return Response({'providers': performance})


class AIFeaturesViewSet(viewsets.ViewSet):
    """
    ViewSet for AI-powered email campaign features
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def optimize_subject(self, request):
        """Optimize email subject line"""
        subject = request.data.get('subject', '')
        campaign_type = request.data.get('campaign_type', 'marketing')
        target_audience = request.data.get('target_audience', '')

        if not subject:
            return Response(
                {'error': 'subject is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ai_service = EmailAIService()
        result = ai_service.optimize_subject_line(subject, campaign_type, target_audience)

        return Response(result)

    @action(detail=False, methods=['post'])
    def improve_content(self, request):
        """Improve email content"""
        content = request.data.get('content', '')
        goal = request.data.get('goal', 'engagement')

        if not content:
            return Response(
                {'error': 'content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ai_service = EmailAIService()
        result = ai_service.improve_email_content(content, goal)

        return Response(result)

    @action(detail=False, methods=['post'])
    def personalize_content(self, request):
        """Generate personalized email content"""
        template = request.data.get('template', '')
        recipient_data = request.data.get('recipient_data', {})
        tone = request.data.get('tone', 'professional')

        if not template:
            return Response(
                {'error': 'template is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ai_service = EmailAIService()
        personalized = ai_service.generate_personalized_content(template, recipient_data, tone)

        return Response({'personalized_content': personalized})

    @action(detail=False, methods=['post'])
    def predict_send_time(self, request):
        """Predict optimal send time for a recipient"""
        recipient_history = request.data.get('recipient_history', [])
        campaign_type = request.data.get('campaign_type', 'marketing')

        ai_service = EmailAIService()
        prediction = ai_service.predict_optimal_send_time(recipient_history, campaign_type)

        return Response(prediction)

    @action(detail=False, methods=['post'])
    def generate_ab_variants(self, request):
        """Generate A/B test variants"""
        element = request.data.get('element', 'subject')
        content = request.data.get('content', '')
        num_variants = int(request.data.get('num_variants', 3))

        if not content:
            return Response(
                {'error': 'content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ai_service = EmailAIService()
        variants = ai_service.generate_ab_test_variants(element, content, num_variants)

        return Response({'variants': variants})

    @action(detail=False, methods=['post'])
    def analyze_performance(self, request):
        """Analyze campaign performance with AI insights"""
        campaign_stats = request.data.get('campaign_stats', {})
        industry_benchmarks = request.data.get('industry_benchmarks')

        ai_service = EmailAIService()
        analysis = ai_service.analyze_campaign_performance(campaign_stats, industry_benchmarks)

        return Response(analysis)

    @action(detail=False, methods=['post'])
    def suggest_segments(self, request):
        """Suggest segment criteria for better targeting"""
        campaign_goal = request.data.get('campaign_goal', '')
        existing_segments = request.data.get('existing_segments', [])

        if not campaign_goal:
            return Response(
                {'error': 'campaign_goal is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ai_service = EmailAIService()
        suggestions = ai_service.suggest_segment_criteria(campaign_goal, existing_segments)

        return Response(suggestions)

    @action(detail=False, methods=['post'])
    def generate_drip_sequence(self, request):
        """Generate a drip campaign sequence"""
        goal = request.data.get('goal', '')
        duration_days = int(request.data.get('duration_days', 14))
        target_audience = request.data.get('target_audience', '')

        if not goal:
            return Response(
                {'error': 'goal is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ai_service = EmailAIService()
        sequence = ai_service.generate_drip_sequence(goal, duration_days, target_audience)

        return Response(sequence)

    @action(detail=False, methods=['post'])
    def predict_unsubscribe_risk(self, request):
        """Predict if recipient is at risk of unsubscribing"""
        recipient_data = request.data.get('recipient_data', {})
        campaign_data = request.data.get('campaign_data', {})

        ai_service = EmailAIService()
        risk = ai_service.predict_unsubscribe_risk(recipient_data, campaign_data)

        return Response(risk)

    @action(detail=False, methods=['post'])
    def calculate_spam_score(self, request):
        """Calculate spam score for template"""
        content = request.data.get('content', '')
        subject = request.data.get('subject', '')

        if not content or not subject:
            return Response(
                {'error': 'Both content and subject are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        template_engine = TemplateEngine()
        spam_score = template_engine.calculate_spam_score(content, subject)

        return Response({
            'spam_score': spam_score,
            'rating': 'low' if spam_score < 30 else 'medium' if spam_score < 60 else 'high'
        })


class TemplateToolsViewSet(viewsets.ViewSet):
    """
    ViewSet for template-related tools
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def validate(self, request):
        """Validate template syntax"""
        content = request.data.get('content', '')

        if not content:
            return Response(
                {'error': 'content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        engine = TemplateEngine()
        is_valid, error = engine.validate_template(content)

        return Response({
            'valid': is_valid,
            'error': error
        })

    @action(detail=False, methods=['post'])
    def preview(self, request):
        """Preview template with sample data"""
        content = request.data.get('content', '')

        if not content:
            return Response(
                {'error': 'content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        engine = TemplateEngine()
        preview = engine.preview_with_sample_data(content)

        return Response({
            'preview_html': preview
        })

    @action(detail=False, methods=['post'])
    def extract_variables(self, request):
        """Extract variables from template"""
        content = request.data.get('content', '')

        if not content:
            return Response(
                {'error': 'content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        engine = TemplateEngine()
        variables = engine.extract_variables(content)

        return Response({
            'variables': variables
        })
