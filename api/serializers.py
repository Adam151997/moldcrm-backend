from rest_framework import serializers
from crm.models import Lead, Contact, Deal
from users.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'phone', 'department', 'account']
        read_only_fields = ['id', 'email', 'account']

class LeadSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']

class DealSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source='contact.__str__', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    class Meta:
        model = Deal
        fields = [
            'id', 'name', 'contact', 'contact_name', 'assigned_to', 'assigned_to_name',
            'amount', 'stage', 'expected_close_date', 'probability', 
            'created_by', 'created_at', 'updated_at', 'account'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']