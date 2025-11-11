from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Sum, Q
from crm.models import Lead, Contact, Deal
from .serializers import LeadSerializer, ContactSerializer, DealSerializer

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class IsAccountUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return hasattr(request, 'account') and request.user.is_authenticated

class LeadViewSet(viewsets.ModelViewSet):
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]
    queryset = Lead.objects.all()  # Add this line
    
    def get_queryset(self):
        return Lead.objects.filter(account=self.request.account)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, account=self.request.account)

class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]
    queryset = Contact.objects.all()  # Add this line
    
    def get_queryset(self):
        return Contact.objects.filter(account=self.request.account)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, account=self.request.account)

class DealViewSet(viewsets.ModelViewSet):
    serializer_class = DealSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]
    queryset = Deal.objects.all()  # Add this line
    
    def get_queryset(self):
        return Deal.objects.filter(account=self.request.account)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, account=self.request.account)

class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]
    
    def get(self, request):
        account = request.account
        
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
