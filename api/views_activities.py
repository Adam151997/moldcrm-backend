from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from crm.models import Activity, Note
from .serializers import ActivitySerializer, NoteSerializer
from .permissions import IsAccountUser

class ActivityViewSet(viewsets.ModelViewSet):
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]
    
    def get_queryset(self):
        return Activity.objects.filter(account=self.request.user.account)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, account=self.request.user.account)
    
    @action(detail=True, methods=['patch'])
    def mark_completed(self, request, pk=None):
        try:
            activity = self.get_object()
            activity.completed = True
            activity.save()
            
            serializer = self.get_serializer(activity)
            return Response(serializer.data)
            
        except Activity.DoesNotExist:
            return Response(
                {'error': 'Activity not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        activities = self.get_queryset().order_by('-created_at')[:20]
        serializer = self.get_serializer(activities, many=True)
        return Response(serializer.data)

class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountUser]
    
    def get_queryset(self):
        return Note.objects.filter(account=self.request.user.account)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, account=self.request.user.account)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        notes = self.get_queryset().order_by('-created_at')[:20]
        serializer = self.get_serializer(notes, many=True)
        return Response(serializer.data)