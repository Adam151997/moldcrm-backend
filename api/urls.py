from django.urls import path, include
from rest_framework.authtoken import views
from . import views as api_views
from .views_auth import CustomAuthToken
from .views_email_campaigns import (
    SegmentViewSet, CampaignABTestViewSet, DripCampaignViewSet,
    DripCampaignStepViewSet, AnalyticsViewSet, AIFeaturesViewSet,
    TemplateToolsViewSet
)
from integrations.webhooks import views as webhook_views
from integrations.plugins import webhook_views as plugin_webhook_views

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

    # Notes
    path('notes/', api_views.NoteViewSet.as_view({'get': 'list', 'post': 'create'}), name='notes-list'),
    path('notes/<int:pk>/', api_views.NoteViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='notes-detail'),

    # Attachments
    path('attachments/', api_views.AttachmentViewSet.as_view({'get': 'list', 'post': 'create'}), name='attachments-list'),
    path('attachments/<int:pk>/', api_views.AttachmentViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}), name='attachments-detail'),

    # Tasks
    path('tasks/', api_views.TaskViewSet.as_view({'get': 'list', 'post': 'create'}), name='tasks-list'),
    path('tasks/<int:pk>/', api_views.TaskViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='tasks-detail'),

    # Activity Logs
    path('activity-logs/', api_views.ActivityLogViewSet.as_view({'get': 'list'}), name='activity-logs-list'),
    path('activity-logs/<int:pk>/', api_views.ActivityLogViewSet.as_view({'get': 'retrieve'}), name='activity-logs-detail'),

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

    # AI Agent (New - Replaces AI Insights)
    path('ai-agent/query/', api_views.AIAgentViewSet.as_view({'post': 'query'}), name='ai-agent-query'),
    path('ai-agent/suggestions/', api_views.AIAgentViewSet.as_view({'post': 'suggestions'}), name='ai-agent-suggestions'),

    # AI Insights (DEPRECATED - Use AI Agent instead)
    path('ai-insights/', api_views.AIInsightViewSet.as_view({'get': 'list'}), name='ai-insights-list'),
    path('ai-insights/<int:pk>/', api_views.AIInsightViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='ai-insights-detail'),
    path('ai-insights/generate-lead-score/', api_views.AIInsightViewSet.as_view({'post': 'generate_lead_score'}), name='ai-insights-lead-score'),
    path('ai-insights/generate-deal-prediction/', api_views.AIInsightViewSet.as_view({'post': 'generate_deal_prediction'}), name='ai-insights-deal-prediction'),

    # Email Templates & Campaigns
    path('email-templates/', api_views.EmailTemplateViewSet.as_view({'get': 'list', 'post': 'create'}), name='email-templates-list'),
    path('email-templates/<int:pk>/', api_views.EmailTemplateViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='email-templates-detail'),
    path('email-campaigns/', api_views.EmailCampaignViewSet.as_view({'get': 'list', 'post': 'create'}), name='email-campaigns-list'),
    path('email-campaigns/<int:pk>/', api_views.EmailCampaignViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='email-campaigns-detail'),

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

    # Plugin Integration Endpoints
    path('plugins/', api_views.PluginViewSet.as_view({'get': 'list', 'post': 'create'}), name='plugins-list'),
    path('plugins/<int:pk>/', api_views.PluginViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='plugins-detail'),
    path('plugins/<int:pk>/oauth-url/', api_views.PluginViewSet.as_view({'get': 'oauth_url'}), name='plugins-oauth-url'),
    path('plugins/<int:pk>/oauth-callback/', api_views.PluginViewSet.as_view({'post': 'oauth_callback'}), name='plugins-oauth-callback'),
    path('plugins/<int:pk>/verify/', api_views.PluginViewSet.as_view({'post': 'verify'}), name='plugins-verify'),
    path('plugins/<int:pk>/sync/', api_views.PluginViewSet.as_view({'post': 'sync'}), name='plugins-sync'),
    path('plugins/<int:pk>/account-info/', api_views.PluginViewSet.as_view({'get': 'account_info'}), name='plugins-account-info'),
    path('plugins/<int:pk>/refresh-token/', api_views.PluginViewSet.as_view({'post': 'refresh_token'}), name='plugins-refresh-token'),
    path('plugins/<int:pk>/toggle-active/', api_views.PluginViewSet.as_view({'post': 'toggle_active'}), name='plugins-toggle-active'),

    # Plugin Events
    path('plugin-events/', api_views.PluginEventViewSet.as_view({'get': 'list'}), name='plugin-events-list'),
    path('plugin-events/<int:pk>/', api_views.PluginEventViewSet.as_view({'get': 'retrieve'}), name='plugin-events-detail'),

    # Plugin Sync Logs
    path('plugin-sync-logs/', api_views.PluginSyncLogViewSet.as_view({'get': 'list'}), name='plugin-sync-logs-list'),
    path('plugin-sync-logs/<int:pk>/', api_views.PluginSyncLogViewSet.as_view({'get': 'retrieve'}), name='plugin-sync-logs-detail'),

    # Plugin Webhooks (no authentication required)
    path('webhooks/plugins/google-ads/<int:plugin_id>/', plugin_webhook_views.google_ads_webhook, name='webhook-google-ads'),
    path('webhooks/plugins/meta-ads/<int:plugin_id>/', plugin_webhook_views.meta_ads_webhook, name='webhook-meta-ads'),
    path('webhooks/plugins/tiktok-ads/<int:plugin_id>/', plugin_webhook_views.tiktok_ads_webhook, name='webhook-tiktok-ads'),
    path('webhooks/plugins/shopify/<int:plugin_id>/', plugin_webhook_views.shopify_webhook, name='webhook-shopify'),

    # Enhanced Email Campaign Features
    # Segments
    path('segments/', SegmentViewSet.as_view({'get': 'list', 'post': 'create'}), name='segments-list'),
    path('segments/<int:pk>/', SegmentViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='segments-detail'),
    path('segments/<int:pk>/preview/', SegmentViewSet.as_view({'get': 'preview'}), name='segments-preview'),
    path('segments/<int:pk>/calculate-size/', SegmentViewSet.as_view({'post': 'calculate_size'}), name='segments-calculate-size'),
    path('segments/<int:pk>/performance/', SegmentViewSet.as_view({'get': 'performance'}), name='segments-performance'),
    path('segments/validate-conditions/', SegmentViewSet.as_view({'post': 'validate_conditions'}), name='segments-validate-conditions'),

    # A/B Tests
    path('ab-tests/', CampaignABTestViewSet.as_view({'get': 'list', 'post': 'create'}), name='ab-tests-list'),
    path('ab-tests/<int:pk>/', CampaignABTestViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='ab-tests-detail'),
    path('ab-tests/<int:pk>/results/', CampaignABTestViewSet.as_view({'get': 'results'}), name='ab-tests-results'),
    path('ab-tests/<int:pk>/select-winner/', CampaignABTestViewSet.as_view({'post': 'select_winner'}), name='ab-tests-select-winner'),

    # Drip Campaigns
    path('drip-campaigns/', DripCampaignViewSet.as_view({'get': 'list', 'post': 'create'}), name='drip-campaigns-list'),
    path('drip-campaigns/<int:pk>/', DripCampaignViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='drip-campaigns-detail'),
    path('drip-campaigns/<int:pk>/activate/', DripCampaignViewSet.as_view({'post': 'activate'}), name='drip-campaigns-activate'),
    path('drip-campaigns/<int:pk>/pause/', DripCampaignViewSet.as_view({'post': 'pause'}), name='drip-campaigns-pause'),
    path('drip-campaigns/<int:pk>/enroll-contact/', DripCampaignViewSet.as_view({'post': 'enroll_contact'}), name='drip-campaigns-enroll'),
    path('drip-campaigns/<int:pk>/analytics/', DripCampaignViewSet.as_view({'get': 'analytics'}), name='drip-campaigns-analytics'),
    path('drip-campaigns/<int:pk>/enrollments/', DripCampaignViewSet.as_view({'get': 'enrollments'}), name='drip-campaigns-enrollments'),

    # Drip Campaign Steps
    path('drip-campaign-steps/', DripCampaignStepViewSet.as_view({'get': 'list', 'post': 'create'}), name='drip-steps-list'),
    path('drip-campaign-steps/<int:pk>/', DripCampaignStepViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='drip-steps-detail'),
    path('drip-campaign-steps/reorder/', DripCampaignStepViewSet.as_view({'post': 'reorder'}), name='drip-steps-reorder'),

    # Analytics
    path('email-analytics/campaign-overview/', AnalyticsViewSet.as_view({'get': 'campaign_overview'}), name='analytics-campaign-overview'),
    path('email-analytics/compare-campaigns/', AnalyticsViewSet.as_view({'post': 'compare_campaigns'}), name='analytics-compare-campaigns'),
    path('email-analytics/global-stats/', AnalyticsViewSet.as_view({'get': 'global_stats'}), name='analytics-global-stats'),
    path('email-analytics/contact-engagement/', AnalyticsViewSet.as_view({'get': 'contact_engagement'}), name='analytics-contact-engagement'),
    path('email-analytics/revenue-attribution/', AnalyticsViewSet.as_view({'get': 'revenue_attribution'}), name='analytics-revenue-attribution'),
    path('email-analytics/provider-performance/', AnalyticsViewSet.as_view({'get': 'provider_performance'}), name='analytics-provider-performance'),

    # AI Features
    path('email-ai/optimize-subject/', AIFeaturesViewSet.as_view({'post': 'optimize_subject'}), name='ai-optimize-subject'),
    path('email-ai/improve-content/', AIFeaturesViewSet.as_view({'post': 'improve_content'}), name='ai-improve-content'),
    path('email-ai/personalize-content/', AIFeaturesViewSet.as_view({'post': 'personalize_content'}), name='ai-personalize-content'),
    path('email-ai/predict-send-time/', AIFeaturesViewSet.as_view({'post': 'predict_send_time'}), name='ai-predict-send-time'),
    path('email-ai/generate-ab-variants/', AIFeaturesViewSet.as_view({'post': 'generate_ab_variants'}), name='ai-generate-ab-variants'),
    path('email-ai/analyze-performance/', AIFeaturesViewSet.as_view({'post': 'analyze_performance'}), name='ai-analyze-performance'),
    path('email-ai/suggest-segments/', AIFeaturesViewSet.as_view({'post': 'suggest_segments'}), name='ai-suggest-segments'),
    path('email-ai/generate-drip-sequence/', AIFeaturesViewSet.as_view({'post': 'generate_drip_sequence'}), name='ai-generate-drip-sequence'),
    path('email-ai/predict-unsubscribe-risk/', AIFeaturesViewSet.as_view({'post': 'predict_unsubscribe_risk'}), name='ai-predict-unsubscribe-risk'),
    path('email-ai/calculate-spam-score/', AIFeaturesViewSet.as_view({'post': 'calculate_spam_score'}), name='ai-calculate-spam-score'),

    # Template Tools
    path('template-tools/validate/', TemplateToolsViewSet.as_view({'post': 'validate'}), name='template-tools-validate'),
    path('template-tools/preview/', TemplateToolsViewSet.as_view({'post': 'preview'}), name='template-tools-preview'),
    path('template-tools/extract-variables/', TemplateToolsViewSet.as_view({'post': 'extract_variables'}), name='template-tools-extract-variables'),
]