from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions  
from django.db.models import Count, Sum, Q
from crm.models import Lead, Contact, Deal
from api.permissions import IsAccountUser 
from api.serializers import LeadSerializer, DealSerializer

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
