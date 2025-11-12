from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Count, Sum, Q
from crm.models import Lead, Contact, Deal
from .serializers import LeadSerializer, ContactSerializer, DealSerializer, UserSerializer

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
            new_stage = request.data.get('stage')
            
            if new_stage not in dict(Deal.STAGE_CHOICES):
                return Response(
                    {'error': 'Invalid stage'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            deal.stage = new_stage
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
        
        stage_counts = Deal.objects.filter(account=account).values('stage').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        total_deals = Deal.objects.filter(account=account).count()
        won_deals = Deal.objects.filter(account=account, stage='closed_won').count()
        lost_deals = Deal.objects.filter(account=account, stage='closed_lost').count()
        
        win_rate = (won_deals / (won_deals + lost_deals)) * 100 if (won_deals + lost_deals) > 0 else 0
        
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
        
        lead_stats = Lead.objects.filter(account=account).aggregate(
            total=Count('id'),
            new=Count('id', filter=Q(status='new')),
            contacted=Count('id', filter=Q(status='contacted')),
            qualified=Count('id', filter=Q(status='qualified'))
        )
        
        deal_stats = Deal.objects.filter(account=account).aggregate(
            total_amount=Sum('amount'),
            won_amount=Sum('amount', filter=Q(stage='closed_won')),
            open_deals=Count('id', filter=~Q(stage__in=['closed_won', 'closed_lost']))
        )
        
        recent_leads = Lead.objects.filter(account=account).order_by('-created_at')[:5]
        recent_deals = Deal.objects.filter(account=account).order_by('-created_at')[:5]
        
        return Response({
            'lead_analytics': lead_stats,
            'deal_analytics': deal_stats,
            'recent_leads': LeadSerializer(recent_leads, many=True).data,
            'recent_deals': DealSerializer(recent_deals, many=True).data,
        })