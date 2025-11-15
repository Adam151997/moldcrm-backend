from django.db import models
from accounts.models import Account
from users.models import User
from crm.models import Lead, Contact, Deal


class EmailTemplate(models.Model):
    """
    Email templates for automated communications
    """
    TEMPLATE_TYPES = [
        ('welcome', 'Welcome Email'),
        ('follow_up', 'Follow-up'),
        ('proposal', 'Proposal'),
        ('thank_you', 'Thank You'),
        ('reminder', 'Reminder'),
        ('custom', 'Custom'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='email_templates')
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES)
    subject = models.CharField(max_length=200)
    body_html = models.TextField()
    body_text = models.TextField(blank=True)  # Plain text version
    
    # Variables that can be used in template
    available_variables = models.JSONField(default=list)  # ['{{contact.name}}', '{{deal.amount}}', etc.]
    
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.account.name})"


class EmailCampaign(models.Model):
    """
    Email campaigns for bulk sending
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='email_campaigns')
    name = models.CharField(max_length=200)
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Email providers - can use multiple providers for load balancing
    providers = models.ManyToManyField('EmailProvider', blank=True, related_name='campaigns')
    provider_strategy = models.CharField(
        max_length=20,
        choices=[
            ('priority', 'Priority Order'),
            ('round_robin', 'Round Robin'),
            ('failover', 'Failover Only'),
        ],
        default='priority'
    )

    # Recipients
    recipient_filter = models.JSONField(default=dict)  # Query filter for recipients
    
    # Schedule
    scheduled_at = models.DateTimeField(null=True, blank=True)
    
    # Stats
    total_recipients = models.IntegerField(default=0)
    sent_count = models.IntegerField(default=0)
    opened_count = models.IntegerField(default=0)
    clicked_count = models.IntegerField(default=0)
    bounced_count = models.IntegerField(default=0)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.status}"


class Email(models.Model):
    """
    Individual emails sent/received
    """
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('failed', 'Failed'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='emails')
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.SET_NULL, null=True, blank=True, related_name='emails')
    provider = models.ForeignKey('EmailProvider', on_delete=models.SET_NULL, null=True, blank=True, related_name='emails')

    # Email details
    from_email = models.EmailField()
    to_email = models.EmailField()
    subject = models.CharField(max_length=200)
    body_html = models.TextField()
    body_text = models.TextField(blank=True)

    # Provider-specific metadata
    provider_message_id = models.CharField(max_length=500, blank=True)  # Message ID from provider
    
    # Related objects
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='emails')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='emails')
    deal = models.ForeignKey(Deal, on_delete=models.SET_NULL, null=True, blank=True, related_name='emails')
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    tracking_id = models.CharField(max_length=100, unique=True, blank=True)
    
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} to {self.to_email}"


class EmailProvider(models.Model):
    """
    Email service provider configurations (SendGrid, Mailgun, etc.)
    """
    PROVIDER_TYPES = [
        ('sendgrid', 'SendGrid'),
        ('mailgun', 'Mailgun'),
        ('mailchimp', 'Mailchimp (Mandrill)'),
        ('brevo', 'Brevo (Sendinblue)'),
        ('klaviyo', 'Klaviyo'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='email_providers')
    provider_type = models.CharField(max_length=50, choices=PROVIDER_TYPES)
    name = models.CharField(max_length=200)  # User-friendly name

    # API Credentials (will be encrypted)
    api_key = models.CharField(max_length=1000, blank=True)
    api_secret = models.CharField(max_length=1000, blank=True)  # For providers that need it

    # Sender Configuration
    sender_email = models.EmailField()
    sender_name = models.CharField(max_length=200)

    # Provider-specific settings (domain, region, etc.)
    config = models.JSONField(default=dict)

    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    # Quota tracking
    daily_limit = models.IntegerField(default=0, help_text="0 means unlimited")
    monthly_limit = models.IntegerField(default=0, help_text="0 means unlimited")
    sent_today = models.IntegerField(default=0)
    sent_this_month = models.IntegerField(default=0)

    # Error tracking
    last_error = models.TextField(blank=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)

    # Priority for multi-provider sending (lower number = higher priority)
    priority = models.IntegerField(default=0)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priority', 'name']
        unique_together = [['account', 'provider_type', 'sender_email']]

    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"

    def increment_sent_count(self):
        """Increment sent counters"""
        self.sent_today += 1
        self.sent_this_month += 1
        self.last_sent_at = models.functions.Now()
        self.save(update_fields=['sent_today', 'sent_this_month', 'last_sent_at'])

    def check_quota(self):
        """Check if provider has available quota"""
        if self.daily_limit > 0 and self.sent_today >= self.daily_limit:
            return False, "Daily limit reached"
        if self.monthly_limit > 0 and self.sent_this_month >= self.monthly_limit:
            return False, "Monthly limit reached"
        return True, "OK"

    def get_masked_api_key(self):
        """Return masked API key for display"""
        if not self.api_key:
            return ""
        if len(self.api_key) <= 8:
            return "****"
        return f"{self.api_key[:4]}...{self.api_key[-4:]}"


class Webhook(models.Model):
    """
    Webhooks for external integrations
    """
    EVENT_TYPES = [
        ('lead.created', 'Lead Created'),
        ('lead.updated', 'Lead Updated'),
        ('contact.created', 'Contact Created'),
        ('contact.updated', 'Contact Updated'),
        ('deal.created', 'Deal Created'),
        ('deal.updated', 'Deal Updated'),
        ('deal.won', 'Deal Won'),
        ('deal.lost', 'Deal Lost'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='webhooks')
    name = models.CharField(max_length=200)
    url = models.URLField(max_length=500)
    event_types = models.JSONField(default=list)  # List of events to trigger on
    
    # Authentication
    secret = models.CharField(max_length=255, blank=True)
    headers = models.JSONField(default=dict)  # Custom headers to send
    
    is_active = models.BooleanField(default=True)
    
    # Stats
    total_calls = models.IntegerField(default=0)
    failed_calls = models.IntegerField(default=0)
    last_called_at = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.account.name})"


class WebhookLog(models.Model):
    """
    Log of webhook calls
    """
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    webhook = models.ForeignKey(Webhook, on_delete=models.CASCADE, related_name='logs')
    event_type = models.CharField(max_length=50)
    payload = models.JSONField()
    response_code = models.IntegerField(null=True)
    response_body = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.webhook.name} - {self.event_type} - {self.status}"


class ExternalIntegration(models.Model):
    """
    External platform integrations (Zapier, Make, etc.)
    """
    PLATFORM_TYPES = [
        ('zapier', 'Zapier'),
        ('make', 'Make (Integromat)'),
        ('n8n', 'n8n'),
        ('custom_api', 'Custom API'),
        ('slack', 'Slack'),
        ('google_sheets', 'Google Sheets'),
        ('hubspot', 'HubSpot'),
        ('salesforce', 'Salesforce'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='integrations')
    platform = models.CharField(max_length=50, choices=PLATFORM_TYPES)
    name = models.CharField(max_length=200)

    # Credentials (encrypted)
    api_key = models.CharField(max_length=500, blank=True)
    api_secret = models.CharField(max_length=500, blank=True)
    access_token = models.CharField(max_length=500, blank=True)
    refresh_token = models.CharField(max_length=500, blank=True)
    config = models.JSONField(default=dict)  # Platform-specific configuration

    is_active = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.get_platform_display()}"


class Plugin(models.Model):
    """
    Plugin extensions for advertising platforms and e-commerce integrations
    Supports Google Ads, Meta Ads, TikTok Ads, Shopify with user credentials
    """
    PLUGIN_TYPES = [
        ('google_ads', 'Google Ads'),
        ('meta_ads', 'Meta Ads (Facebook & Instagram)'),
        ('tiktok_ads', 'TikTok Ads'),
        ('shopify', 'Shopify'),
    ]

    CATEGORY_CHOICES = [
        ('advertising', 'Advertising Platform'),
        ('ecommerce', 'E-commerce Platform'),
    ]

    STATUS_CHOICES = [
        ('connected', 'Connected'),
        ('disconnected', 'Disconnected'),
        ('error', 'Error'),
        ('pending', 'Pending Authorization'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='plugins')
    plugin_type = models.CharField(max_length=50, choices=PLUGIN_TYPES)
    name = models.CharField(max_length=200, help_text="User-friendly name for this plugin connection")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    # OAuth2 Credentials (encrypted)
    client_id = models.CharField(max_length=1000, blank=True)
    client_secret = models.CharField(max_length=1000, blank=True)
    access_token = models.CharField(max_length=2000, blank=True)
    refresh_token = models.CharField(max_length=2000, blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)

    # Platform-specific configuration
    config = models.JSONField(default=dict, help_text="Platform-specific settings like ad account ID, store domain, etc.")

    # Webhook configuration
    webhook_url = models.URLField(max_length=500, blank=True, help_text="Webhook URL for receiving events from platform")
    webhook_secret = models.CharField(max_length=255, blank=True, help_text="Secret for webhook verification")

    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    # Sync tracking
    last_sync_at = models.DateTimeField(null=True, blank=True)
    sync_frequency = models.IntegerField(default=3600, help_text="Sync frequency in seconds (default: 1 hour)")

    # Error tracking
    last_error = models.TextField(blank=True)
    error_count = models.IntegerField(default=0)

    # Statistics
    total_syncs = models.IntegerField(default=0)
    failed_syncs = models.IntegerField(default=0)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
        unique_together = [['account', 'plugin_type', 'name']]

    def __str__(self):
        return f"{self.name} ({self.get_plugin_type_display()}) - {self.account.name}"

    def get_masked_client_secret(self):
        """Return masked client secret for display"""
        if not self.client_secret:
            return ""
        if len(self.client_secret) <= 8:
            return "****"
        return f"{self.client_secret[:4]}...{self.client_secret[-4:]}"

    def get_masked_access_token(self):
        """Return masked access token for display"""
        if not self.access_token:
            return ""
        if len(self.access_token) <= 8:
            return "****"
        return f"{self.access_token[:4]}...{self.access_token[-4:]}"

    def is_token_expired(self):
        """Check if OAuth token is expired"""
        if not self.token_expires_at:
            return False
        from django.utils import timezone
        return timezone.now() >= self.token_expires_at

    def increment_sync_count(self):
        """Increment sync counter"""
        self.total_syncs += 1
        self.last_sync_at = models.functions.Now()
        self.save(update_fields=['total_syncs', 'last_sync_at'])

    def increment_error_count(self):
        """Increment error counter"""
        self.error_count += 1
        self.failed_syncs += 1
        self.save(update_fields=['error_count', 'failed_syncs'])


class PluginEvent(models.Model):
    """
    Events received from plugin platforms via webhooks
    """
    EVENT_TYPES = [
        # Google Ads events
        ('google_ads.campaign.created', 'Google Ads - Campaign Created'),
        ('google_ads.campaign.updated', 'Google Ads - Campaign Updated'),
        ('google_ads.ad.created', 'Google Ads - Ad Created'),
        ('google_ads.conversion', 'Google Ads - Conversion'),

        # Meta Ads events
        ('meta_ads.campaign.created', 'Meta Ads - Campaign Created'),
        ('meta_ads.campaign.updated', 'Meta Ads - Campaign Updated'),
        ('meta_ads.ad.created', 'Meta Ads - Ad Created'),
        ('meta_ads.lead', 'Meta Ads - Lead Generated'),

        # TikTok Ads events
        ('tiktok_ads.campaign.created', 'TikTok Ads - Campaign Created'),
        ('tiktok_ads.campaign.updated', 'TikTok Ads - Campaign Updated'),
        ('tiktok_ads.ad.created', 'TikTok Ads - Ad Created'),

        # Shopify events
        ('shopify.order.created', 'Shopify - Order Created'),
        ('shopify.order.updated', 'Shopify - Order Updated'),
        ('shopify.customer.created', 'Shopify - Customer Created'),
        ('shopify.product.created', 'Shopify - Product Created'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    ]

    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=100, choices=EVENT_TYPES)
    event_id = models.CharField(max_length=255, help_text="Platform's event/webhook ID")

    # Event data
    payload = models.JSONField(help_text="Raw webhook payload from platform")
    processed_data = models.JSONField(default=dict, help_text="Processed/normalized data")

    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)

    # CRM linking - automatically create/update CRM records
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='plugin_events')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='plugin_events')
    deal = models.ForeignKey(Deal, on_delete=models.SET_NULL, null=True, blank=True, related_name='plugin_events')

    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['plugin', 'event_type']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.plugin.name} - {self.event_type} - {self.status}"


class PluginSyncLog(models.Model):
    """
    Logs of plugin synchronization operations
    """
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('partial', 'Partial Success'),
        ('failed', 'Failed'),
    ]

    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE, related_name='sync_logs')
    sync_type = models.CharField(max_length=100, help_text="Type of sync operation (e.g., campaigns, orders, customers)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    # Sync statistics
    records_fetched = models.IntegerField(default=0)
    records_created = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)

    # Details
    details = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.plugin.name} - {self.sync_type} - {self.status}"
