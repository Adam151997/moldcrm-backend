from django.contrib import admin
from .models import BusinessTemplate, AppliedTemplate


@admin.register(BusinessTemplate)
class BusinessTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_active', 'created_at']
    list_filter = ['template_type', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(AppliedTemplate)
class AppliedTemplateAdmin(admin.ModelAdmin):
    list_display = ['template', 'account', 'applied_by', 'applied_at']
    list_filter = ['applied_at', 'template__template_type']
    search_fields = ['account__name', 'template__name']
    ordering = ['-applied_at']
