from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Count, Sum, Q
from django.db import transaction
from crm.models import Lead, Contact, Deal, PipelineStage
from custom_objects.models import CustomObject, CustomField, CustomObjectRecord
from .serializers import (
    LeadSerializer, ContactSerializer, DealSerializer, UserSerializer,
    PipelineStageSerializer, CustomFieldSerializer, CustomObjectSerializer,
    CustomObjectRecordSerializer, PluginSerializer, PluginEventSerializer,
    PluginSyncLogSerializer
)

class IsAccountUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'account')

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class LeadViewSet(viewsets.ModelViewSet):
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]
    
    def get_queryset(self):
        return Lead.objects.filter(account=self.request.user.account)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, account=self.request.user.account)

class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]
    
    def get_queryset(self):
        return Contact.objects.filter(account=self.request.user.account)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, account=self.request.user.account)
    
    @action(detail=False, methods=['post'])
    def convert_from_lead(self, request):
        lead_id = request.data.get('lead_id')
        try:
            lead = Lead.objects.get(id=lead_id, account=request.user.account)
            contact = Contact.objects.create(
                first_name=lead.first_name,
                last_name=lead.last_name,
                email=lead.email,
                phone=lead.phone or '',
                company=lead.company or '',
                lead=lead,
                account=request.user.account,
                created_by=request.user
            )
            # Update lead status
            lead.status = 'converted'
            lead.save()
            
            serializer = ContactSerializer(contact)
            return Response(serializer.data)
        except Lead.DoesNotExist:
            return Response(
                {"error": "Lead not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

class DealViewSet(viewsets.ModelViewSet):
    serializer_class = DealSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]
    
    def get_queryset(self):
        return Deal.objects.filter(account=self.request.user.account)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, account=self.request.user.account)
    
    @action(detail=True, methods=['patch'])
    def update_stage(self, request, pk=None):
        try:
            deal = self.get_object()

            # Support both legacy stage names and custom pipeline stage IDs
            new_stage = request.data.get('stage')
            pipeline_stage_id = request.data.get('pipeline_stage')

            # Log request data for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"update_stage called with data: {request.data}")

            if pipeline_stage_id:
                # Using custom pipeline stages
                try:
                    pipeline_stage = PipelineStage.objects.get(
                        id=pipeline_stage_id,
                        account=request.user.account
                    )
                    deal.pipeline_stage = pipeline_stage
                    # Update legacy stage field based on pipeline stage properties
                    if pipeline_stage.is_closed and pipeline_stage.is_won:
                        deal.stage = 'closed_won'
                    elif pipeline_stage.is_closed and not pipeline_stage.is_won:
                        deal.stage = 'closed_lost'
                    else:
                        deal.stage = 'prospect'  # Default for open stages
                except PipelineStage.DoesNotExist:
                    return Response(
                        {'error': 'Pipeline stage not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            elif new_stage:
                # Using legacy stage names (for backward compatibility)
                if new_stage not in dict(Deal.STAGE_CHOICES):
                    return Response(
                        {'error': 'Invalid stage'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                deal.stage = new_stage
                deal.pipeline_stage = None
            else:
                return Response(
                    {'error': 'Either stage or pipeline_stage must be provided', 'received_data': request.data},
                    status=status.HTTP_400_BAD_REQUEST
                )

            deal.save()

            serializer = self.get_serializer(deal)
            return Response(serializer.data)

        except Deal.DoesNotExist:
            return Response(
                {'error': 'Deal not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def pipeline_analytics(self, request):
        account = request.user.account
        
        # Stage counts
        stage_counts = Deal.objects.filter(account=account).values('stage').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Win rate calculation
        total_deals = Deal.objects.filter(account=account).count()
        won_deals = Deal.objects.filter(account=account, stage='closed_won').count()
        lost_deals = Deal.objects.filter(account=account, stage='closed_lost').count()
        
        win_rate = (won_deals / (won_deals + lost_deals)) * 100 if (won_deals + lost_deals) > 0 else 0
        
        # Pipeline value by stage
        pipeline_value = Deal.objects.filter(
            account=account, 
            stage__in=['prospect', 'qualification', 'proposal', 'negotiation']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return Response({
            'stage_counts': list(stage_counts),
            'win_rate': round(win_rate, 2),
            'pipeline_value': float(pipeline_value) if pipeline_value else 0,
            'total_deals': total_deals,
            'won_deals': won_deals,
            'lost_deals': lost_deals,
        })

class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]
    
    def get(self, request):
        account = request.user.account
        
        # Lead statistics
        lead_stats = Lead.objects.filter(account=account).aggregate(
            total=Count('id'),
            new=Count('id', filter=Q(status='new')),
            contacted=Count('id', filter=Q(status='contacted')),
            qualified=Count('id', filter=Q(status='qualified'))
        )
        
        # Deal pipeline
        deal_stats = Deal.objects.filter(account=account).aggregate(
            total_amount=Sum('amount'),
            won_amount=Sum('amount', filter=Q(stage='closed_won')),
            open_deals=Count('id', filter=~Q(stage__in=['closed_won', 'closed_lost']))
        )
        
        # Recent activity
        recent_leads = Lead.objects.filter(account=account).order_by('-created_at')[:5]
        recent_deals = Deal.objects.filter(account=account).order_by('-created_at')[:5]
        
        return Response({
            'lead_analytics': lead_stats,
            'deal_analytics': deal_stats,
            'recent_leads': LeadSerializer(recent_leads, many=True).data,
            'recent_deals': DealSerializer(recent_deals, many=True).data,
        })

class PipelineStageViewSet(viewsets.ModelViewSet):
    """ViewSet for managing custom pipeline stages"""
    serializer_class = PipelineStageSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]

    def get_queryset(self):
        return PipelineStage.objects.filter(account=self.request.user.account)

    def perform_create(self, serializer):
        # Auto-increment order if not provided
        account = self.request.user.account
        max_order = PipelineStage.objects.filter(account=account).count()
        serializer.save(account=account, order=max_order)

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """Reorder pipeline stages based on provided order"""
        stages_order = request.data.get('stages', [])  # Expected format: [{'id': 1, 'order': 0}, {'id': 2, 'order': 1}, ...]

        try:
            with transaction.atomic():
                for stage_data in stages_order:
                    stage_id = stage_data.get('id')
                    new_order = stage_data.get('order')

                    stage = PipelineStage.objects.get(
                        id=stage_id,
                        account=request.user.account
                    )
                    stage.order = new_order
                    stage.save()

            return Response({'status': 'success', 'message': 'Stages reordered successfully'})
        except PipelineStage.DoesNotExist:
            return Response(
                {'error': 'One or more stages not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class CustomFieldViewSet(viewsets.ModelViewSet):
    """ViewSet for managing custom fields"""
    serializer_class = CustomFieldSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]

    def get_queryset(self):
        queryset = CustomField.objects.filter(account=self.request.user.account)

        # Filter by entity_type if provided
        entity_type = self.request.query_params.get('entity_type', None)
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)

        return queryset

    def perform_create(self, serializer):
        # Auto-increment order if not provided
        account = self.request.user.account
        entity_type = serializer.validated_data.get('entity_type', 'custom')
        max_order = CustomField.objects.filter(
            account=account,
            entity_type=entity_type
        ).count()
        serializer.save(account=account, order=max_order)

    def create(self, request, *args, **kwargs):
        # Log request data for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"CustomField create called with data: {request.data}")

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"CustomField validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class CustomObjectViewSet(viewsets.ModelViewSet):
    """ViewSet for managing custom objects"""
    serializer_class = CustomObjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]

    def get_queryset(self):
        return CustomObject.objects.filter(account=self.request.user.account)

    def perform_create(self, serializer):
        serializer.save(
            account=self.request.user.account,
            created_by=self.request.user
        )

class CustomObjectRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for managing custom object records"""
    serializer_class = CustomObjectRecordSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]

    def get_queryset(self):
        queryset = CustomObjectRecord.objects.filter(custom_object__account=self.request.user.account)

        # Filter by custom_object if provided
        custom_object_id = self.request.query_params.get('custom_object', None)
        if custom_object_id:
            queryset = queryset.filter(custom_object_id=custom_object_id)

        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
# ========================================
# Business Templates ViewSets
# ========================================

class BusinessTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for browsing available business templates"""
    from .serializers import BusinessTemplateSerializer
    serializer_class = BusinessTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]

    def get_queryset(self):
        from templates.models import BusinessTemplate
        return BusinessTemplate.objects.filter(is_active=True)

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Apply a template to the user's account"""
        from templates.models import BusinessTemplate, AppliedTemplate
        from crm.models import PipelineStage
        from custom_objects.models import CustomField
        
        template = self.get_object()
        account = request.user.account
        
        # Create applied template record
        applied_template = AppliedTemplate.objects.create(
            account=account,
            template=template,
            applied_by=request.user
        )
        
        # Apply pipeline stages
        for stage_config in template.pipeline_stages:
            PipelineStage.objects.get_or_create(
                account=account,
                name=stage_config['name'],
                defaults={
                    'display_name': stage_config['display_name'],
                    'color': stage_config.get('color', '#3B82F6'),
                    'is_closed': stage_config.get('is_closed', False),
                    'is_won': stage_config.get('is_won', False),
                    'order': stage_config.get('order', 0),
                }
            )
        
        # Apply custom fields
        for field_config in template.custom_fields:
            CustomField.objects.get_or_create(
                account=account,
                name=field_config['name'],
                entity_type=field_config.get('entity_type', 'deal'),
                defaults={
                    'display_name': field_config['display_name'],
                    'field_type': field_config['field_type'],
                    'required': field_config.get('required', False),
                    'default_value': field_config.get('default_value', ''),
                    'options': field_config.get('options'),
                    'order': field_config.get('order', 0),
                }
            )
        
        from .serializers import AppliedTemplateSerializer
        serializer = AppliedTemplateSerializer(applied_template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AppliedTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing applied templates"""
    from .serializers import AppliedTemplateSerializer
    serializer_class = AppliedTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]

    def get_queryset(self):
        from templates.models import AppliedTemplate
        return AppliedTemplate.objects.filter(account=self.request.user.account)


# ========================================
# Automation ViewSets
# ========================================

class WorkflowViewSet(viewsets.ModelViewSet):
    """ViewSet for managing workflows"""
    from .serializers import WorkflowSerializer
    serializer_class = WorkflowSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]

    def get_queryset(self):
        from automation.models import Workflow
        return Workflow.objects.filter(account=self.request.user.account)

    def perform_create(self, serializer):
        serializer.save(
            account=self.request.user.account,
            created_by=self.request.user
        )


class AIInsightViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AI insights.

    DEPRECATED: This endpoint is deprecated and will be removed in a future version.
    Please use the new AI Agent endpoint at /api/v1/ai-agent/query/ instead.
    The AI Agent provides a more flexible conversational interface with the same capabilities.
    """
    from .serializers import AIInsightSerializer
    serializer_class = AIInsightSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]

    def get_queryset(self):
        from automation.models import AIInsight
        return AIInsight.objects.filter(account=self.request.user.account)

    @action(detail=False, methods=['post'])
    def generate_lead_score(self, request):
        """
        Generate AI lead score.

        DEPRECATED: Use /api/v1/ai-agent/query/ with a natural language query instead.
        Example: POST {"query": "Score lead #123"}
        """
        from automation.services import GeminiAIService
        from automation.models import AIInsight
        from crm.models import Lead

        lead_id = request.data.get('lead_id')
        try:
            lead = Lead.objects.get(id=lead_id, account=request.user.account)
            lead_data = {
                'first_name': lead.first_name,
                'last_name': lead.last_name,
                'company': lead.company,
                'status': lead.status,
                'source': lead.source,
                'notes': lead.notes,
            }

            ai_service = GeminiAIService()
            result = ai_service.generate_lead_score(lead_data)

            # Create insight record
            insight = AIInsight.objects.create(
                account=request.user.account,
                lead=lead,
                insight_type='lead_score',
                title=f"Lead Score: {result.get('score', 0)}/100",
                content=result.get('reasoning', ''),
                confidence_score=result.get('score', 0) / 100,
                metadata={
                    'recommendations': result.get('recommendations', []),
                    'deprecated_warning': 'This endpoint is deprecated. Use /api/v1/ai-agent/query/ instead.'
                }
            )

            from .serializers import AIInsightSerializer
            serializer = AIInsightSerializer(insight)
            response_data = serializer.data
            response_data['_deprecated'] = True
            response_data['_migration_note'] = 'Please migrate to /api/v1/ai-agent/query/ for better AI capabilities'
            return Response(response_data)
        except Lead.DoesNotExist:
            return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def generate_deal_prediction(self, request):
        """
        Generate AI deal prediction.

        DEPRECATED: Use /api/v1/ai-agent/query/ with a natural language query instead.
        Example: POST {"query": "What's the likelihood of deal #456 closing?"}
        """
        from automation.services import GeminiAIService
        from automation.models import AIInsight
        from crm.models import Deal

        deal_id = request.data.get('deal_id')
        try:
            deal = Deal.objects.get(id=deal_id, account=request.user.account)
            deal_data = {
                'name': deal.name,
                'amount': str(deal.amount) if deal.amount else '0',
                'stage': deal.stage,
                'expected_close_date': str(deal.expected_close_date) if deal.expected_close_date else None,
                'probability': deal.probability,
                'contact_name': deal.contact.__str__() if deal.contact else 'Unknown',
            }

            ai_service = GeminiAIService()
            result = ai_service.predict_deal_outcome(deal_data)

            # Create insight record
            insight = AIInsight.objects.create(
                account=request.user.account,
                deal=deal,
                insight_type='deal_prediction',
                title=f"Deal Prediction: {result.get('probability', 0)}% likely to close",
                content=f"Predicted close: {result.get('predicted_close_date', 'uncertain')}",
                confidence_score=result.get('probability', 0) / 100,
                metadata={
                    'insights': result.get('insights', []),
                    'risk_factors': result.get('risk_factors', []),
                    'deprecated_warning': 'This endpoint is deprecated. Use /api/v1/ai-agent/query/ instead.'
                }
            )

            from .serializers import AIInsightSerializer
            serializer = AIInsightSerializer(insight)
            response_data = serializer.data
            response_data['_deprecated'] = True
            response_data['_migration_note'] = 'Please migrate to /api/v1/ai-agent/query/ for better AI capabilities'
            return Response(response_data)
        except Deal.DoesNotExist:
            return Response({'error': 'Deal not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIAgentViewSet(viewsets.ViewSet):
    """
    AI Agent for conversational CRM interactions.
    Replaces the old AI Insights system with a natural language interface.
    """
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]

    @action(detail=False, methods=['post'])
    def query(self, request):
        """
        Process a natural language query with the AI Agent.

        Request body:
        {
            "query": "Show me my pipeline summary",
            "conversation_history": []  // Optional for multi-turn conversations
        }
        """
        from automation.services.agent_service import AgentService
        from automation.models import AIInsight

        query = request.data.get('query')
        conversation_history = request.data.get('conversation_history', [])

        if not query:
            return Response(
                {'error': 'Query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Initialize agent and process query
            agent = AgentService()
            result = agent.process_query(
                query=query,
                account_id=request.user.account.id,
                user_id=request.user.id,
                conversation_history=conversation_history
            )

            # Log the interaction for audit trail
            if result.get('success'):
                # Determine insight type based on function calls
                function_calls = result.get('function_calls', [])
                insight_type = 'agent_query'

                if function_calls:
                    first_call = function_calls[0]['function']
                    if 'lead' in first_call:
                        insight_type = 'agent_lead'
                    elif 'deal' in first_call:
                        insight_type = 'agent_deal'
                    elif 'pipeline' in first_call:
                        insight_type = 'agent_report'

                AIInsight.objects.create(
                    account=request.user.account,
                    insight_type=insight_type,
                    title=f"Agent Query: {query[:100]}",
                    content=result.get('response') or 'Processing...',  # Ensure never None
                    confidence_score=1.0 if result.get('success') else 0.0,
                    metadata={
                        'query': query,
                        'function_calls': function_calls,
                        'conversation_turn': len(conversation_history) // 2 + 1
                    }
                )

            return Response(result)

        except Exception as e:
            return Response(
                {
                    'success': False,
                    'response': f'An error occurred: {str(e)}',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def suggestions(self, request):
        """
        Get contextual suggestions for what the user might want to do next.

        Request body:
        {
            "context": {
                "recent_action": "viewed_pipeline",
                "current_view": "dashboard"
            }
        }
        """
        from automation.services.agent_service import AgentService

        context = request.data.get('context', {})

        try:
            agent = AgentService()
            suggestions = agent.generate_suggestions(context)

            return Response({
                'success': True,
                'suggestions': suggestions
            })

        except Exception as e:
            return Response(
                {
                    'success': False,
                    'suggestions': [
                        "Show me my pipeline summary",
                        "What are my newest leads?",
                        "Create a new lead"
                    ],
                    'error': str(e)
                },
                status=status.HTTP_200_OK  # Still return suggestions on error
            )


# ========================================
# Email & Integration ViewSets
# ========================================

class EmailTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email templates"""
    from .serializers import EmailTemplateSerializer
    serializer_class = EmailTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]

    def get_queryset(self):
        from integrations.models import EmailTemplate
        return EmailTemplate.objects.filter(account=self.request.user.account)

    def perform_create(self, serializer):
        serializer.save(
            account=self.request.user.account,
            created_by=self.request.user
        )


class EmailCampaignViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email campaigns"""
    from .serializers import EmailCampaignSerializer
    serializer_class = EmailCampaignSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]

    def get_queryset(self):
        from integrations.models import EmailCampaign
        return EmailCampaign.objects.filter(account=self.request.user.account)

    def perform_create(self, serializer):
        serializer.save(
            account=self.request.user.account,
            created_by=self.request.user
        )


class ExternalIntegrationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing external integrations"""
    from .serializers import ExternalIntegrationSerializer
    serializer_class = ExternalIntegrationSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]

    def get_queryset(self):
        from integrations.models import ExternalIntegration
        return ExternalIntegration.objects.filter(account=self.request.user.account)

    def perform_create(self, serializer):
        serializer.save(
            account=self.request.user.account,
            created_by=self.request.user
        )


class EmailProviderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email providers"""
    from .serializers import EmailProviderSerializer
    serializer_class = EmailProviderSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]

    def get_queryset(self):
        from integrations.models import EmailProvider
        return EmailProvider.objects.filter(account=self.request.user.account)

    def perform_create(self, serializer):
        serializer.save(
            account=self.request.user.account,
            created_by=self.request.user
        )

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify provider API key and sender email"""
        from integrations.services.email_provider_service import EmailProviderService

        provider = self.get_object()

        is_valid, message = EmailProviderService.validate_provider(provider)

        if is_valid:
            provider.is_verified = True
            provider.save(update_fields=['is_verified'])
            return Response({
                'success': True,
                'message': message
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def test_send(self, request, pk=None):
        """Send a test email through this provider"""
        from integrations.services.email_provider_service import EmailProviderService

        provider = self.get_object()

        # Get test email address from request
        test_email = request.data.get('test_email')
        if not test_email:
            return Response({
                'success': False,
                'message': 'test_email is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create test email data
        email_data = {
            'to_email': test_email,
            'subject': 'Test Email from MoldCRM',
            'body_html': '<h1>Test Email</h1><p>This is a test email from your email provider configuration.</p>',
            'body_text': 'Test Email - This is a test email from your email provider configuration.',
        }

        # Send email
        response = EmailProviderService.send_email(provider, email_data)

        if response.success:
            return Response({
                'success': True,
                'message': 'Test email sent successfully',
                'message_id': response.message_id
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': response.error_message
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get provider statistics"""
        from integrations.services.email_provider_service import EmailProviderService

        provider = self.get_object()
        stats = EmailProviderService.get_provider_stats(provider)

        return Response(stats, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle provider active status"""
        provider = self.get_object()
        provider.is_active = not provider.is_active
        provider.save(update_fields=['is_active'])

        return Response({
            'success': True,
            'is_active': provider.is_active
        }, status=status.HTTP_200_OK)


class PluginViewSet(viewsets.ModelViewSet):
    """ViewSet for managing plugin integrations (Google Ads, Meta Ads, TikTok Ads, Shopify)"""
    serializer_class = PluginSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]

    def get_queryset(self):
        from integrations.models import Plugin
        return Plugin.objects.filter(account=self.request.user.account)

    def perform_create(self, serializer):
        serializer.save(
            account=self.request.user.account,
            created_by=self.request.user
        )

    @action(detail=True, methods=['get'])
    def oauth_url(self, request, pk=None):
        """Get OAuth authorization URL for plugin"""
        from integrations.plugins.plugin_service import PluginService
        import secrets

        plugin = self.get_object()

        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        request.session[f'oauth_state_{plugin.id}'] = state

        # Get redirect URI from request or use default
        redirect_uri = request.query_params.get('redirect_uri', request.build_absolute_uri('/api/plugins/oauth/callback/'))

        try:
            oauth_url = PluginService.initiate_oauth(plugin, redirect_uri, state)
            return Response({
                'success': True,
                'oauth_url': oauth_url,
                'state': state
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def oauth_callback(self, request, pk=None):
        """Handle OAuth callback"""
        from integrations.plugins.plugin_service import PluginService

        plugin = self.get_object()

        # Verify state
        state = request.data.get('state')
        expected_state = request.session.get(f'oauth_state_{plugin.id}')

        if state != expected_state:
            return Response({
                'success': False,
                'message': 'Invalid state parameter'
            }, status=status.HTTP_400_BAD_REQUEST)

        code = request.data.get('code')
        redirect_uri = request.data.get('redirect_uri', request.build_absolute_uri('/api/plugins/oauth/callback/'))

        if not code:
            return Response({
                'success': False,
                'message': 'Authorization code is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        success, message = PluginService.complete_oauth(plugin, code, redirect_uri)

        if success:
            # Clean up session
            request.session.pop(f'oauth_state_{plugin.id}', None)

            return Response({
                'success': True,
                'message': message
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify plugin connection"""
        from integrations.plugins.plugin_service import PluginService

        plugin = self.get_object()
        success, message = PluginService.verify_connection(plugin)

        if success:
            return Response({
                'success': True,
                'message': message
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Trigger data synchronization"""
        from integrations.plugins.plugin_service import PluginService

        plugin = self.get_object()
        sync_type = request.data.get('sync_type')

        if not sync_type:
            return Response({
                'success': False,
                'message': 'sync_type is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Trigger async sync task or run sync directly
            result = PluginService.sync_plugin_data(plugin, sync_type, **request.data)

            if result.success:
                return Response({
                    'success': True,
                    'message': 'Sync completed successfully',
                    'records_fetched': result.records_fetched,
                    'records_created': result.records_created,
                    'records_updated': result.records_updated,
                    'details': result.details
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': result.error
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def account_info(self, request, pk=None):
        """Get account information from platform"""
        from integrations.plugins.plugin_service import PluginService

        plugin = self.get_object()
        account_info = PluginService.get_account_info(plugin)

        return Response(account_info, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def refresh_token(self, request, pk=None):
        """Manually refresh OAuth token"""
        from integrations.plugins.plugin_service import PluginService

        plugin = self.get_object()
        success = PluginService.refresh_token_if_needed(plugin)

        if success:
            return Response({
                'success': True,
                'message': 'Token refreshed successfully'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Token refresh failed'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle plugin active status"""
        plugin = self.get_object()
        plugin.is_active = not plugin.is_active
        plugin.save(update_fields=['is_active'])

        return Response({
            'success': True,
            'is_active': plugin.is_active
        }, status=status.HTTP_200_OK)


class PluginEventViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing plugin events"""
    serializer_class = PluginEventSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]

    def get_queryset(self):
        from integrations.models import PluginEvent
        # Filter by account through plugin relationship
        return PluginEvent.objects.filter(plugin__account=self.request.user.account).select_related('plugin', 'lead', 'contact', 'deal')


class PluginSyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing plugin sync logs"""
    serializer_class = PluginSyncLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]

    def get_queryset(self):
        from integrations.models import PluginSyncLog
        # Filter by account through plugin relationship
        return PluginSyncLog.objects.filter(plugin__account=self.request.user.account).select_related('plugin')
