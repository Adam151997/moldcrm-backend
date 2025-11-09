from django.db import models
from accounts.models import Account
from users.models import User

class CustomObject(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='📄')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.display_name

class CustomField(models.Model):
    FIELD_TYPES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('boolean', 'Checkbox'),
        ('select', 'Dropdown'),
        ('email', 'Email'),
        ('phone', 'Phone'),
    ]
    
    custom_object = models.ForeignKey(CustomObject, on_delete=models.CASCADE, related_name='fields')
    name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    required = models.BooleanField(default=False)
    options = models.JSONField(blank=True, null=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.custom_object.name}.{self.name}"

class CustomObjectRecord(models.Model):
    custom_object = models.ForeignKey(CustomObject, on_delete=models.CASCADE)
    data = models.JSONField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.custom_object.name} Record #{self.id}"