from django.db import models
from django.utils import timezone
from accounts.models import Account
from users.models import User
from accounts.managers import AccountManager

class CustomObject(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='📄')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = AccountManager()
    
    def __str__(self):
        return self.display_name

class CustomField(models.Model):
    FIELD_TYPES = [
        ('text', 'Text'),
        ('textarea', 'Long Text'),
        ('number', 'Number'),
        ('currency', 'Currency'),
        ('date', 'Date'),
        ('boolean', 'Yes/No'),
        ('select', 'Dropdown'),
        ('email', 'Email'),
        ('phone', 'Phone'),
    ]

    ENTITY_TYPES = [
        ('deal', 'Deal'),
        ('contact', 'Contact'),
        ('lead', 'Lead'),
        ('custom', 'Custom Object'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    custom_object = models.ForeignKey(CustomObject, on_delete=models.CASCADE, related_name='fields', null=True, blank=True)
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES, default='custom')  # Type of entity this field belongs to
    name = models.CharField(max_length=100)  # Internal name (e.g., 'custom_budget')
    display_name = models.CharField(max_length=100)  # Display name (e.g., 'Budget')
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    required = models.BooleanField(default=False)
    default_value = models.CharField(max_length=255, blank=True)
    options = models.JSONField(blank=True, null=True)  # For select fields: list of options
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        if self.custom_object:
            return f"{self.custom_object.name}.{self.name}"
        return f"{self.entity_type}.{self.name}"

class CustomObjectRecord(models.Model):
    custom_object = models.ForeignKey(CustomObject, on_delete=models.CASCADE)
    data = models.JSONField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = AccountManager()
    
    def __str__(self):
        return f"{self.custom_object.name} Record #{self.id}"