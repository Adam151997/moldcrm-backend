from rest_framework import serializers
from crm.models import Lead, Contact, Deal, PipelineStage
from custom_objects.models import CustomObject, CustomField, CustomObjectRecord
from templates.models import BusinessTemplate, AppliedTemplate
from automation.models import Workflow, WorkflowExecution, AIInsight
from integrations.models import (EmailTemplate, EmailCampaign, Email, EmailProvider,
                                Webhook, WebhookLog, ExternalIntegration,
                                Plugin, PluginEvent, PluginSyncLog)
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

class EmailProviderSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    provider_display = serializers.CharField(source='get_provider_type_display', read_only=True)
    masked_api_key = serializers.CharField(source='get_masked_api_key', read_only=True)

    class Meta:
        model = EmailProvider
        fields = [
            'id', 'provider_type', 'provider_display', 'name',
            'sender_email', 'sender_name', 'config',
            'is_active', 'is_verified', 'priority',
            'daily_limit', 'monthly_limit', 'sent_today', 'sent_this_month',
            'last_error', 'last_sent_at', 'masked_api_key',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_by', 'created_by_name', 'created_at', 'updated_at', 'account',
            'is_verified', 'sent_today', 'sent_this_month', 'last_error', 'last_sent_at',
            'provider_display', 'masked_api_key'
        ]
        extra_kwargs = {
            'api_key': {'write_only': True},
            'api_secret': {'write_only': True},
        }

    def create(self, validated_data):
        from integrations.services.encryption import encrypt_api_key

        # Encrypt API keys before saving
        if 'api_key' in validated_data and validated_data['api_key']:
            validated_data['api_key'] = encrypt_api_key(validated_data['api_key'])

        if 'api_secret' in validated_data and validated_data['api_secret']:
            validated_data['api_secret'] = encrypt_api_key(validated_data['api_secret'])

        return super().create(validated_data)

    def update(self, instance, validated_data):
        from integrations.services.encryption import encrypt_api_key

        # Encrypt API keys before saving if they were updated
        if 'api_key' in validated_data and validated_data['api_key']:
            validated_data['api_key'] = encrypt_api_key(validated_data['api_key'])

        if 'api_secret' in validated_data and validated_data['api_secret']:
            validated_data['api_secret'] = encrypt_api_key(validated_data['api_secret'])

        return super().update(instance, validated_data)


# Plugin Integration Serializers
class PluginSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    plugin_display = serializers.CharField(source='get_plugin_type_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    masked_client_secret = serializers.CharField(source='get_masked_client_secret', read_only=True)
    masked_access_token = serializers.CharField(source='get_masked_access_token', read_only=True)
    is_token_expired_flag = serializers.BooleanField(source='is_token_expired', read_only=True)

    class Meta:
        model = Plugin
        fields = [
            'id', 'plugin_type', 'plugin_display', 'name', 'category', 'category_display',
            'status', 'status_display', 'is_active', 'is_verified',
            'config', 'webhook_url', 'webhook_secret',
            'last_sync_at', 'sync_frequency', 'last_error', 'error_count',
            'total_syncs', 'failed_syncs', 'token_expires_at', 'is_token_expired_flag',
            'masked_client_secret', 'masked_access_token',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_by', 'created_by_name', 'created_at', 'updated_at', 'account',
            'is_verified', 'last_sync_at', 'last_error', 'error_count',
            'total_syncs', 'failed_syncs', 'token_expires_at',
            'plugin_display', 'category_display', 'status_display',
            'masked_client_secret', 'masked_access_token', 'is_token_expired_flag'
        ]
        extra_kwargs = {
            'client_id': {'write_only': True},
            'client_secret': {'write_only': True},
            'access_token': {'write_only': True},
            'refresh_token': {'write_only': True},
        }

    def create(self, validated_data):
        from integrations.services.encryption import encrypt_value
        from integrations.plugins.plugin_service import PluginService

        plugin_type = validated_data.get('plugin_type')

        # Check if centralized credentials are available
        use_centralized = PluginService.use_centralized_credentials(plugin_type)

        # If using centralized credentials, client_id/secret are optional
        if not use_centralized:
            # Validate that user provided credentials
            if not validated_data.get('client_id') or not validated_data.get('client_secret'):
                from rest_framework import serializers as drf_serializers
                raise drf_serializers.ValidationError({
                    'client_id': 'Client ID is required when centralized credentials are not configured.',
                    'client_secret': 'Client secret is required when centralized credentials are not configured.'
                })

        # Encrypt credentials before saving (only if provided)
        if 'client_id' in validated_data and validated_data.get('client_id'):
            validated_data['client_id'] = encrypt_value(validated_data['client_id'])

        if 'client_secret' in validated_data and validated_data.get('client_secret'):
            validated_data['client_secret'] = encrypt_value(validated_data['client_secret'])

        if 'access_token' in validated_data and validated_data.get('access_token'):
            validated_data['access_token'] = encrypt_value(validated_data['access_token'])

        if 'refresh_token' in validated_data and validated_data.get('refresh_token'):
            validated_data['refresh_token'] = encrypt_value(validated_data['refresh_token'])

        # Set category based on plugin type
        if plugin_type in ['google_ads', 'meta_ads', 'tiktok_ads']:
            validated_data['category'] = 'advertising'
        elif plugin_type == 'shopify':
            validated_data['category'] = 'ecommerce'

        return super().create(validated_data)

    def update(self, instance, validated_data):
        from integrations.services.encryption import encrypt_value

        # Encrypt credentials before saving if they were updated
        if 'client_id' in validated_data and validated_data['client_id']:
            validated_data['client_id'] = encrypt_value(validated_data['client_id'])

        if 'client_secret' in validated_data and validated_data['client_secret']:
            validated_data['client_secret'] = encrypt_value(validated_data['client_secret'])

        if 'access_token' in validated_data and validated_data.get('access_token'):
            validated_data['access_token'] = encrypt_value(validated_data['access_token'])

        if 'refresh_token' in validated_data and validated_data.get('refresh_token'):
            validated_data['refresh_token'] = encrypt_value(validated_data['refresh_token'])

        return super().update(instance, validated_data)


class PluginEventSerializer(serializers.ModelSerializer):
    plugin_name = serializers.CharField(source='plugin.name', read_only=True)
    plugin_type = serializers.CharField(source='plugin.plugin_type', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PluginEvent
        fields = [
            'id', 'plugin', 'plugin_name', 'plugin_type',
            'event_type', 'event_type_display', 'event_id',
            'payload', 'processed_data', 'status', 'status_display',
            'error_message', 'lead', 'contact', 'deal',
            'processed_at', 'created_at'
        ]
        read_only_fields = ['created_at', 'processed_at']


class PluginSyncLogSerializer(serializers.ModelSerializer):
    plugin_name = serializers.CharField(source='plugin.name', read_only=True)
    plugin_type = serializers.CharField(source='plugin.plugin_type', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PluginSyncLog
        fields = [
            'id', 'plugin', 'plugin_name', 'plugin_type',
            'sync_type', 'status', 'status_display',
            'records_fetched', 'records_created', 'records_updated', 'records_failed',
            'details', 'error_message',
            'started_at', 'completed_at', 'duration_seconds'
        ]
        read_only_fields = ['started_at', 'completed_at', 'duration_seconds']
