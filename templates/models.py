from django.db import models
from accounts.models import Account
from users.models import User


class BusinessTemplate(models.Model):
    """
    Predefined business templates for different industries
    """
    TEMPLATE_TYPES = [
        ('saas', 'SaaS'),
        ('real_estate', 'Real Estate'),
        ('ecommerce', 'E-commerce'),
        ('consulting', 'Consulting'),
        ('agency', 'Agency'),
        ('custom', 'Custom'),
    ]

    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='📋')
    is_active = models.BooleanField(default=True)

    # Template configuration (JSON)
    pipeline_stages = models.JSONField(default=list)  # Preset pipeline stages
    custom_fields = models.JSONField(default=list)  # Preset custom fields
    automation_rules = models.JSONField(default=list)  # Preset automations
    email_templates = models.JSONField(default=list)  # Preset email templates

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class AppliedTemplate(models.Model):
    """
    Track which templates have been applied to which accounts
    """
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='applied_templates')
    template = models.ForeignKey(BusinessTemplate, on_delete=models.CASCADE)
    applied_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    configuration = models.JSONField(default=dict)  # Store customizations

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.template.name} applied to {self.account.name}"
