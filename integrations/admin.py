from django.contrib import admin
from .models import (
    EmailTemplate, EmailCampaign, Email, EmailProvider,
    ExternalIntegration
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


@admin.register(EmailProvider)
class EmailProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider_type', 'sender_email', 'account', 'is_active', 'is_verified', 'sent_today', 'sent_this_month']
    list_filter = ['provider_type', 'is_active', 'is_verified', 'created_at']
    search_fields = ['name', 'sender_email', 'account__name']
    ordering = ['priority', 'name']
    readonly_fields = ['created_at', 'updated_at', 'last_sent_at', 'sent_today', 'sent_this_month']


@admin.register(ExternalIntegration)
class ExternalIntegrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'platform', 'account', 'is_active', 'last_sync_at']
    list_filter = ['platform', 'is_active', 'created_at']
    search_fields = ['name', 'account__name']
    ordering = ['name']
