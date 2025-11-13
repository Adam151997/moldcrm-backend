from rest_framework import serializers
from crm.models import Lead, Contact, Deal, PipelineStage
from custom_objects.models import CustomObject, CustomField, CustomObjectRecord
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
        fields = ['id', 'custom_object', 'entity_type', 'name', 'display_name', 'field_type',
                  'required', 'default_value', 'options', 'order', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

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