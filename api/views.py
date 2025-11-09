from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from crm.models import Lead, Contact, Deal
from .serializers import LeadSerializer, ContactSerializer, DealSerializer

class IsAccountUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return hasattr(request, 'account') and request.user.is_authenticated

class LeadViewSet(viewsets.ModelViewSet):
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]
    
    def get_queryset(self):
        return Lead.objects.filter(account=self.request.account)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, account=self.request.account)

class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]
    
    def get_queryset(self):
        return Contact.objects.filter(account=self.request.account)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, account=self.request.account)

class DealViewSet(viewsets.ModelViewSet):
    serializer_class = DealSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]
    
    def get_queryset(self):
        return Deal.objects.filter(account=self.request.account)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, account=self.request.account)