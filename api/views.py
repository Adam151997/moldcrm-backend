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
    CustomObjectRecordSerializer
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