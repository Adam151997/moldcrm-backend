from rest_framework import serializers
from crm.models import Lead, Contact, Deal, Activity, Note
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
    activities = serializers.SerializerMethodField()
    notes_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'account']
    
    def get_activities(self, obj):
        return ActivitySerializer(obj.activities.all(), many=True).data
    
    def get_notes_list(self, obj):
        return NoteSerializer(obj.note_entries.all(), many=True).data

class ContactSerializer(serializers.ModelSerializer):
    lead_source = serializers.CharField(source='lead.__str__', read_only=True)
    deal_count = serializers.SerializerMethodField()
    activities = serializers.SerializerMethodField()
    notes_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Contact
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone', 
            'company', 'title', 'department', 'lead', 'lead_source',
            'deal_count', 'custom_data', 'activities', 'notes_list',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'account']
    
    def get_deal_count(self, obj):
        return obj.deals.count()
    
    def get_activities(self, obj):
        return ActivitySerializer(obj.activities.all(), many=True).data
    
    def get_notes_list(self, obj):
        return NoteSerializer(obj.note_entries.all(), many=True).data

class DealSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source='contact.__str__', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    activities = serializers.SerializerMethodField()
    notes_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Deal
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'account']
    
    def get_activities(self, obj):
        return ActivitySerializer(obj.activities.all(), many=True).data
    
    def get_notes_list(self, obj):
        return NoteSerializer(obj.note_entries.all(), many=True).data

class ActivitySerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    related_object = serializers.SerializerMethodField()
    
    class Meta:
        model = Activity
        fields = [
            'id', 'activity_type', 'title', 'description', 'due_date', 
            'completed', 'completed_at', 'lead', 'contact', 'deal',
            'created_by', 'created_by_name', 'related_object', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'account']
    
    def get_related_object(self, obj):
        if obj.lead:
            return {'type': 'lead', 'id': obj.lead.id, 'name': str(obj.lead)}
        elif obj.contact:
            return {'type': 'contact', 'id': obj.contact.id, 'name': str(obj.contact)}
        elif obj.deal:
            return {'type': 'deal', 'id': obj.deal.id, 'name': str(obj.deal)}
        return None
    
    def validate(self, data):
        # Ensure at least one related object is provided
        if not any([data.get('lead'), data.get('contact'), data.get('deal')]):
            raise serializers.ValidationError("At least one related object (lead, contact, or deal) is required.")
        return data

class NoteSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    related_object = serializers.SerializerMethodField()
    
    class Meta:
        model = Note
        fields = [
            'id', 'content', 'lead', 'contact', 'deal',
            'created_by', 'created_by_name', 'related_object', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'account']
    
    def get_related_object(self, obj):
        if obj.lead:
            return {'type': 'lead', 'id': obj.lead.id, 'name': str(obj.lead)}
        elif obj.contact:
            return {'type': 'contact', 'id': obj.contact.id, 'name': str(obj.contact)}
        elif obj.deal:
            return {'type': 'deal', 'id': obj.deal.id, 'name': str(obj.deal)}
        return None
    
    def validate(self, data):
        # Ensure at least one related object is provided
        if not any([data.get('lead'), data.get('contact'), data.get('deal')]):
            raise serializers.ValidationError("At least one related object (lead, contact, or deal) is required.")
        return data