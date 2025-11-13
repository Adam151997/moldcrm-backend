from django.contrib import admin
from .models import Workflow, WorkflowExecution, AIInsight


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ['name', 'account', 'status', 'trigger_type', 'execution_count', 'created_at']
    list_filter = ['status', 'trigger_type', 'created_at']
    search_fields = ['name', 'account__name']
    ordering = ['-created_at']


@admin.register(WorkflowExecution)
class WorkflowExecutionAdmin(admin.ModelAdmin):
    list_display = ['workflow', 'status', 'started_at', 'completed_at']
    list_filter = ['status', 'started_at']
    search_fields = ['workflow__name']
    ordering = ['-started_at']


@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = ['title', 'insight_type', 'account', 'confidence_score', 'is_read', 'created_at']
    list_filter = ['insight_type', 'is_read', 'created_at']
    search_fields = ['title', 'content', 'account__name']
    ordering = ['-created_at']
