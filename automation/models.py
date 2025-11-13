from django.db import models
from accounts.models import Account
from users.models import User
from crm.models import Lead, Contact, Deal


class Workflow(models.Model):
    """
    Automation workflows with triggers and actions
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('draft', 'Draft'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='workflows')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Trigger configuration
    trigger_type = models.CharField(max_length=50)  # 'deal_created', 'stage_changed', 'field_updated', etc.
    trigger_config = models.JSONField(default=dict)  # Additional trigger settings
    
    # Actions to perform
    actions = models.JSONField(default=list)  # List of actions to execute
    
    # Stats
    execution_count = models.IntegerField(default=0)
    last_executed_at = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.account.name})"


class WorkflowExecution(models.Model):
    """
    Log of workflow executions
    """
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('running', 'Running'),
    ]

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='executions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')
    
    # Context data
    trigger_data = models.JSONField(default=dict)
    actions_executed = models.JSONField(default=list)
    error_message = models.TextField(blank=True)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.workflow.name} - {self.status} at {self.started_at}"


class AIInsight(models.Model):
    """
    AI-generated insights using Gemini API
    """
    INSIGHT_TYPES = [
        ('lead_score', 'Lead Scoring'),
        ('deal_prediction', 'Deal Prediction'),
        ('sentiment', 'Sentiment Analysis'),
        ('suggestion', 'Smart Suggestion'),
        ('summary', 'Summary'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='ai_insights')
    insight_type = models.CharField(max_length=50, choices=INSIGHT_TYPES)
    
    # Related objects (nullable - could be for general account insights)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='ai_insights')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='ai_insights')
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, null=True, blank=True, related_name='ai_insights')
    
    # Insight data
    title = models.CharField(max_length=200)
    content = models.TextField()
    confidence_score = models.FloatField(default=0.0)  # 0-1 confidence
    metadata = models.JSONField(default=dict)  # Additional AI response data
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_insight_type_display()}: {self.title}"
