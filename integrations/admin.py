from django.contrib import admin
from .models import (
    EmailTemplate, EmailCampaign, Email, 
    Webhook, WebhookLog, ExternalIntegration
)


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'account', 'is_active', 'created_at']
    list_filter = ['template_type', 'is_active', 'created_at']
    search_fields = ['name', 'subject', 'account__name']
    ordering = ['name']


@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'account', 'status', 'total_recipients', 'sent_count', 'opened_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'account__name']
    ordering = ['-created_at']


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ['subject', 'to_email', 'status', 'account', 'sent_at']
    list_filter = ['status', 'sent_at']
    search_fields = ['subject', 'to_email', 'from_email']
    ordering = ['-created_at']


@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ['name', 'account', 'url', 'is_active', 'total_calls', 'failed_calls']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'url', 'account__name']
    ordering = ['name']


@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    list_display = ['webhook', 'event_type', 'status', 'response_code', 'created_at']
    list_filter = ['status', 'event_type', 'created_at']
    search_fields = ['webhook__name', 'event_type']
    ordering = ['-created_at']


@admin.register(ExternalIntegration)
class ExternalIntegrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'platform', 'account', 'is_active', 'last_sync_at']
    list_filter = ['platform', 'is_active', 'created_at']
    search_fields = ['name', 'account__name']
    ordering = ['name']
