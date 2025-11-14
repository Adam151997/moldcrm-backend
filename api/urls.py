from django.urls import path, include
from rest_framework.authtoken import views
from . import views as api_views
from .views_auth import CustomAuthToken
from integrations.webhooks import views as webhook_views

urlpatterns = [
    # Authentication - USE CUSTOM AUTH
    path('auth/login/', CustomAuthToken.as_view(), name='login'),
    
    # User endpoints
    path('users/profile/', api_views.UserProfileView.as_view(), name='user-profile'),
    
    # CRM endpoints
    path('leads/', api_views.LeadViewSet.as_view({'get': 'list', 'post': 'create'}), name='leads-list'),
    path('leads/<int:pk>/', api_views.LeadViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='leads-detail'),
    
    path('contacts/', api_views.ContactViewSet.as_view({'get': 'list', 'post': 'create'}), name='contacts-list'),
    path('contacts/<int:pk>/', api_views.ContactViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='contacts-detail'),
    path('contacts/convert_from_lead/', api_views.ContactViewSet.as_view({'post': 'convert_from_lead'}), name='convert-from-lead'),
    
    # Deal endpoints with custom actions
    path('deals/', api_views.DealViewSet.as_view({'get': 'list', 'post': 'create'}), name='deals-list'),
    path('deals/<int:pk>/', api_views.DealViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='deals-detail'),
    path('deals/<int:pk>/update_stage/', api_views.DealViewSet.as_view({'patch': 'update_stage'}), name='deal-update-stage'),
    path('deals/pipeline_analytics/', api_views.DealViewSet.as_view({'get': 'pipeline_analytics'}), name='pipeline-analytics'),
    
    # Dashboard
    path('dashboard/', api_views.DashboardView.as_view(), name='dashboard'),

    # Pipeline Stages
    path('pipeline-stages/', api_views.PipelineStageViewSet.as_view({'get': 'list', 'post': 'create'}), name='pipeline-stages-list'),
    path('pipeline-stages/<int:pk>/', api_views.PipelineStageViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='pipeline-stages-detail'),
    path('pipeline-stages/reorder/', api_views.PipelineStageViewSet.as_view({'post': 'reorder'}), name='pipeline-stages-reorder'),

    # Custom Fields
    path('custom-fields/', api_views.CustomFieldViewSet.as_view({'get': 'list', 'post': 'create'}), name='custom-fields-list'),
    path('custom-fields/<int:pk>/', api_views.CustomFieldViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='custom-fields-detail'),

    # Custom Objects
    path('custom-objects/', api_views.CustomObjectViewSet.as_view({'get': 'list', 'post': 'create'}), name='custom-objects-list'),
    path('custom-objects/<int:pk>/', api_views.CustomObjectViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='custom-objects-detail'),

    # Custom Object Records
    path('custom-object-records/', api_views.CustomObjectRecordViewSet.as_view({'get': 'list', 'post': 'create'}), name='custom-object-records-list'),
    path('custom-object-records/<int:pk>/', api_views.CustomObjectRecordViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='custom-object-records-detail'),

    # Business Templates
    path('templates/', api_views.BusinessTemplateViewSet.as_view({'get': 'list'}), name='templates-list'),
    path('templates/<int:pk>/', api_views.BusinessTemplateViewSet.as_view({'get': 'retrieve'}), name='templates-detail'),
    path('templates/<int:pk>/apply/', api_views.BusinessTemplateViewSet.as_view({'post': 'apply'}), name='templates-apply'),
    path('applied-templates/', api_views.AppliedTemplateViewSet.as_view({'get': 'list'}), name='applied-templates-list'),

    # Workflows & Automation
    path('workflows/', api_views.WorkflowViewSet.as_view({'get': 'list', 'post': 'create'}), name='workflows-list'),
    path('workflows/<int:pk>/', api_views.WorkflowViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='workflows-detail'),

    # AI Insights
    path('ai-insights/', api_views.AIInsightViewSet.as_view({'get': 'list'}), name='ai-insights-list'),
    path('ai-insights/<int:pk>/', api_views.AIInsightViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='ai-insights-detail'),
    path('ai-insights/generate-lead-score/', api_views.AIInsightViewSet.as_view({'post': 'generate_lead_score'}), name='ai-insights-lead-score'),
    path('ai-insights/generate-deal-prediction/', api_views.AIInsightViewSet.as_view({'post': 'generate_deal_prediction'}), name='ai-insights-deal-prediction'),

    # Email Templates & Campaigns
    path('email-templates/', api_views.EmailTemplateViewSet.as_view({'get': 'list', 'post': 'create'}), name='email-templates-list'),
    path('email-templates/<int:pk>/', api_views.EmailTemplateViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='email-templates-detail'),
    path('email-campaigns/', api_views.EmailCampaignViewSet.as_view({'get': 'list', 'post': 'create'}), name='email-campaigns-list'),
    path('email-campaigns/<int:pk>/', api_views.EmailCampaignViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='email-campaigns-detail'),

    # Webhooks
    path('webhooks/', api_views.WebhookViewSet.as_view({'get': 'list', 'post': 'create'}), name='webhooks-list'),
    path('webhooks/<int:pk>/', api_views.WebhookViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='webhooks-detail'),

    # External Integrations
    path('integrations/', api_views.ExternalIntegrationViewSet.as_view({'get': 'list', 'post': 'create'}), name='integrations-list'),
    path('integrations/<int:pk>/', api_views.ExternalIntegrationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='integrations-detail'),

    # Email Providers
    path('email-providers/', api_views.EmailProviderViewSet.as_view({'get': 'list', 'post': 'create'}), name='email-providers-list'),
    path('email-providers/<int:pk>/', api_views.EmailProviderViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='email-providers-detail'),
    path('email-providers/<int:pk>/verify/', api_views.EmailProviderViewSet.as_view({'post': 'verify'}), name='email-providers-verify'),
    path('email-providers/<int:pk>/test-send/', api_views.EmailProviderViewSet.as_view({'post': 'test_send'}), name='email-providers-test-send'),
    path('email-providers/<int:pk>/stats/', api_views.EmailProviderViewSet.as_view({'get': 'stats'}), name='email-providers-stats'),
    path('email-providers/<int:pk>/toggle-active/', api_views.EmailProviderViewSet.as_view({'post': 'toggle_active'}), name='email-providers-toggle-active'),

    # Email Provider Webhooks (no authentication required)
    path('webhooks/email/sendgrid/', webhook_views.SendGridWebhookView.as_view(), name='webhook-sendgrid'),
    path('webhooks/email/mailgun/', webhook_views.MailgunWebhookView.as_view(), name='webhook-mailgun'),
    path('webhooks/email/brevo/', webhook_views.BrevoWebhookView.as_view(), name='webhook-brevo'),
    path('webhooks/email/mailchimp/', webhook_views.MailchimpWebhookView.as_view(), name='webhook-mailchimp'),
    path('webhooks/email/klaviyo/', webhook_views.KlaviyoWebhookView.as_view(), name='webhook-klaviyo'),
]