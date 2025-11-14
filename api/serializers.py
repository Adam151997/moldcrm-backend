from rest_framework import serializers
from crm.models import Lead, Contact, Deal, PipelineStage
from custom_objects.models import CustomObject, CustomField, CustomObjectRecord
from templates.models import BusinessTemplate, AppliedTemplate
from automation.models import Workflow, WorkflowExecution, AIInsight
from integrations.models import EmailTemplate, EmailCampaign, Email, Webhook, WebhookLog, ExternalIntegration
from users.models import User

class UserSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)
    account_id = serializers.IntegerField(source='account.id', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role', 
            'phone', 'department', 'account_id', 'account_name'
        ]
        read_only_fields = ['id', 'email', 'account_id', 'account_name']

class LeadSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'account']

class ContactSerializer(serializers.ModelSerializer):
    lead_source = serializers.CharField(source='lead.__str__', read_only=True)
    deal_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Contact
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone', 
            'company', 'title', 'department', 'lead', 'lead_source',
            'deal_count', 'custom_data', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'account']
    
    def get_deal_count(self, obj):
        return obj.deals.count()

class DealSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source='contact.__str__', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    pipeline_stage_name = serializers.CharField(source='pipeline_stage.display_name', read_only=True, allow_null=True)

    class Meta:
        model = Deal
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'account']

class PipelineStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineStage
        fields = ['id', 'name', 'display_name', 'color', 'is_closed', 'is_won', 'order', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class CustomFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomField
        fields = ['id', 'account', 'custom_object', 'entity_type', 'name', 'display_name', 'field_type',
                  'required', 'default_value', 'options', 'order', 'created_at', 'updated_at']
        read_only_fields = ['account', 'created_at', 'updated_at']

class CustomObjectSerializer(serializers.ModelSerializer):
    fields = CustomFieldSerializer(many=True, read_only=True)

    class Meta:
        model = CustomObject
        fields = ['id', 'name', 'display_name', 'description', 'icon', 'fields', 'created_at']
        read_only_fields = ['created_at']

class CustomObjectRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomObjectRecord
        fields = ['id', 'custom_object', 'data', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at']
# Business Templates Serializers
class BusinessTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessTemplate
        fields = '__all__'

class AppliedTemplateSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    applied_by_name = serializers.CharField(source='applied_by.get_full_name', read_only=True)
    
    class Meta:
        model = AppliedTemplate
        fields = '__all__'
        read_only_fields = ['applied_by', 'applied_at']

# Automation Serializers
class WorkflowSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Workflow
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'account', 'execution_count', 'last_executed_at']

class WorkflowExecutionSerializer(serializers.ModelSerializer):
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    
    class Meta:
        model = WorkflowExecution
        fields = '__all__'
        read_only_fields = ['started_at', 'completed_at']

class AIInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIInsight
        fields = '__all__'
        read_only_fields = ['created_at', 'account']

# Email & Integration Serializers
class EmailTemplateSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = EmailTemplate
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'account']

class EmailCampaignSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = EmailCampaign
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'account', 'sent_count', 'opened_count', 'clicked_count', 'bounced_count']

class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = '__all__'
        read_only_fields = ['created_at', 'account', 'sent_at', 'delivered_at', 'opened_at', 'clicked_at']

class WebhookSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Webhook
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'account', 'total_calls', 'failed_calls', 'last_called_at']

class WebhookLogSerializer(serializers.ModelSerializer):
    webhook_name = serializers.CharField(source='webhook.name', read_only=True)
    
    class Meta:
        model = WebhookLog
        fields = '__all__'
        read_only_fields = ['created_at']

class ExternalIntegrationSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    
    class Meta:
        model = ExternalIntegration
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'account', 'last_sync_at']
        extra_kwargs = {
            'api_key': {'write_only': True},
            'api_secret': {'write_only': True},
            'access_token': {'write_only': True},
            'refresh_token': {'write_only': True},
        }
