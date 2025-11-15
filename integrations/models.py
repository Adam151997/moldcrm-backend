from django.db import models
from accounts.models import Account
from users.models import User
from crm.models import Lead, Contact, Deal


class EmailTemplate(models.Model):
    """
    Email templates for automated communications - ENHANCED
    """
    TEMPLATE_TYPES = [
        ('welcome', 'Welcome Email'),
        ('follow_up', 'Follow-up'),
        ('proposal', 'Proposal'),
        ('thank_you', 'Thank You'),
        ('reminder', 'Reminder'),
        ('newsletter', 'Newsletter'),
        ('promotional', 'Promotional'),
        ('transactional', 'Transactional'),
        ('drip', 'Drip Sequence'),
        ('custom', 'Custom'),
    ]

    CATEGORY_CHOICES = [
        ('marketing', 'Marketing'),
        ('sales', 'Sales'),
        ('support', 'Support'),
        ('transactional', 'Transactional'),
        ('automated', 'Automated'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='email_templates')
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='marketing')

    # Email content
    subject = models.CharField(max_length=200)
    preview_text = models.CharField(max_length=150, blank=True, help_text="Inbox preview text (preheader)")
    body_html = models.TextField()
    body_text = models.TextField(blank=True)  # Plain text version

    # Visual editor support
    design_json = models.JSONField(default=dict, blank=True, help_text="Design structure for visual builder")
    thumbnail = models.URLField(max_length=500, blank=True, help_text="Template preview image")

    # Variables that can be used in template
    available_variables = models.JSONField(default=list)  # ['{{contact.name}}', '{{deal.amount}}', etc.]

    # AI & Optimization
    ai_optimization_score = models.IntegerField(default=0, help_text="AI-generated optimization score (0-100)")
    spam_score = models.FloatField(default=0.0, help_text="Spam probability score")

    # Usage stats
    usage_count = models.IntegerField(default=0, help_text="Number of times template has been used")
    avg_open_rate = models.FloatField(default=0.0, help_text="Average open rate across campaigns")
    avg_click_rate = models.FloatField(default=0.0, help_text="Average click rate across campaigns")

    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['account', 'category']),
            models.Index(fields=['template_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.account.name})"


class Segment(models.Model):
    """
    Advanced recipient segmentation with visual filter builder support
    """
    SEGMENT_TYPES = [
        ('static', 'Static List'),
        ('dynamic', 'Dynamic (Auto-Update)'),
        ('behavioral', 'Behavioral'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='segments')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    segment_type = models.CharField(max_length=20, choices=SEGMENT_TYPES, default='dynamic')

    # Filter conditions (supports complex AND/OR logic)
    filter_conditions = models.JSONField(default=dict, help_text="Visual filter builder conditions")

    # Static list support
    static_contacts = models.ManyToManyField(Contact, blank=True, related_name='static_segments')
    static_leads = models.ManyToManyField(Lead, blank=True, related_name='static_segments')

    # Size tracking
    estimated_size = models.IntegerField(default=0, help_text="Estimated recipient count")
    actual_size = models.IntegerField(default=0, help_text="Actual recipient count (after calculation)")
    last_calculated_at = models.DateTimeField(null=True, blank=True)

    # Auto-update for dynamic segments
    auto_update = models.BooleanField(default=True, help_text="Auto-recalculate before each campaign")

    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['account', 'segment_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.actual_size} recipients)"


class EmailCampaign(models.Model):
    """
    Email campaigns for bulk sending - SIGNIFICANTLY ENHANCED
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]

    CAMPAIGN_TYPES = [
        ('one_time', 'One-Time Broadcast'),
        ('recurring', 'Recurring'),
        ('triggered', 'Triggered/Automated'),
        ('ab_test', 'A/B Test'),
    ]

    SEND_OPTIMIZATION = [
        ('immediate', 'Send Immediately'),
        ('optimal_time', 'Optimal Time (AI)'),
        ('time_zone_aware', 'Time Zone Aware'),
        ('scheduled', 'Scheduled Time'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='email_campaigns')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    campaign_type = models.CharField(max_length=20, choices=CAMPAIGN_TYPES, default='one_time')
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
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

    # Recipients - Enhanced
    segment = models.ForeignKey(Segment, on_delete=models.SET_NULL, null=True, blank=True, related_name='campaigns')
    recipient_filter = models.JSONField(default=dict, help_text="Legacy/simple filter (deprecated, use segment)")

    # Sending options
    send_optimization = models.CharField(max_length=20, choices=SEND_OPTIMIZATION, default='immediate')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    throttle_rate = models.IntegerField(default=0, help_text="Emails per hour (0 = no throttling)")

    # A/B Testing
    ab_test_enabled = models.BooleanField(default=False)
    ab_test_config = models.JSONField(default=dict, blank=True, help_text="A/B test configuration")

    # Link tracking & UTM parameters
    utm_campaign = models.CharField(max_length=200, blank=True)
    utm_source = models.CharField(max_length=100, blank=True, default='moldcrm')
    utm_medium = models.CharField(max_length=100, blank=True, default='email')
    utm_content = models.CharField(max_length=200, blank=True)
    utm_term = models.CharField(max_length=200, blank=True)
    track_clicks = models.BooleanField(default=True)
    track_opens = models.BooleanField(default=True)

    # Goal tracking
    goal_metric = models.CharField(max_length=50, blank=True, help_text="open_rate, click_rate, conversion, revenue")
    goal_value = models.FloatField(default=0.0, help_text="Target value for goal")

    # Enhanced Stats
    total_recipients = models.IntegerField(default=0)
    sent_count = models.IntegerField(default=0)
    delivered_count = models.IntegerField(default=0)
    opened_count = models.IntegerField(default=0)
    unique_opens = models.IntegerField(default=0)
    clicked_count = models.IntegerField(default=0)
    unique_clicks = models.IntegerField(default=0)
    bounced_count = models.IntegerField(default=0)
    hard_bounces = models.IntegerField(default=0)
    soft_bounces = models.IntegerField(default=0)
    unsubscribed_count = models.IntegerField(default=0)
    spam_complaints = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)

    # Conversion & Revenue tracking
    conversion_count = models.IntegerField(default=0)
    revenue_generated = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    # Calculated rates
    delivery_rate = models.FloatField(default=0.0)
    open_rate = models.FloatField(default=0.0)
    click_rate = models.FloatField(default=0.0)
    click_to_open_rate = models.FloatField(default=0.0)
    bounce_rate = models.FloatField(default=0.0)
    unsubscribe_rate = models.FloatField(default=0.0)
    conversion_rate = models.FloatField(default=0.0)

    # Timing
    started_sending_at = models.DateTimeField(null=True, blank=True)
    completed_sending_at = models.DateTimeField(null=True, blank=True)
    send_duration_seconds = models.IntegerField(default=0)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account', 'status']),
            models.Index(fields=['campaign_type', 'status']),
            models.Index(fields=['scheduled_at']),
        ]

    def __str__(self):
        return f"{self.name} - {self.status}"

    def calculate_rates(self):
        """Calculate all campaign rates"""
        if self.sent_count > 0:
            self.delivery_rate = (self.delivered_count / self.sent_count) * 100
            self.bounce_rate = (self.bounced_count / self.sent_count) * 100
            self.unsubscribe_rate = (self.unsubscribed_count / self.sent_count) * 100

        if self.delivered_count > 0:
            self.open_rate = (self.unique_opens / self.delivered_count) * 100
            self.click_rate = (self.unique_clicks / self.delivered_count) * 100
            self.conversion_rate = (self.conversion_count / self.delivered_count) * 100

        if self.unique_opens > 0:
            self.click_to_open_rate = (self.unique_clicks / self.unique_opens) * 100

        self.save(update_fields=[
            'delivery_rate', 'open_rate', 'click_rate', 'click_to_open_rate',
            'bounce_rate', 'unsubscribe_rate', 'conversion_rate'
        ])


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


class CampaignABTest(models.Model):
    """
    A/B Testing for email campaigns
    """
    STATUS_CHOICES = [
        ('testing', 'Testing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, related_name='ab_tests')
    test_name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='testing')

    # Test configuration
    test_element = models.CharField(max_length=50, help_text="subject, from_name, content, send_time")
    variant_a_value = models.TextField(help_text="Value for variant A")
    variant_b_value = models.TextField(help_text="Value for variant B")
    variant_c_value = models.TextField(blank=True, help_text="Optional variant C")
    variant_d_value = models.TextField(blank=True, help_text="Optional variant D")
    variant_e_value = models.TextField(blank=True, help_text="Optional variant E")

    # Traffic split (percentages)
    test_percentage = models.IntegerField(default=20, help_text="Percentage of total for testing")
    variant_a_percentage = models.IntegerField(default=50, help_text="Percentage within test group")
    variant_b_percentage = models.IntegerField(default=50)
    variant_c_percentage = models.IntegerField(default=0)
    variant_d_percentage = models.IntegerField(default=0)
    variant_e_percentage = models.IntegerField(default=0)

    # Win criteria
    win_metric = models.CharField(max_length=50, default='open_rate', help_text="open_rate, click_rate, conversion")
    auto_select_winner = models.BooleanField(default=True)
    hours_to_test = models.IntegerField(default=24, help_text="Duration before selecting winner")

    # Results
    variant_a_sent = models.IntegerField(default=0)
    variant_a_opens = models.IntegerField(default=0)
    variant_a_clicks = models.IntegerField(default=0)
    variant_a_conversions = models.IntegerField(default=0)

    variant_b_sent = models.IntegerField(default=0)
    variant_b_opens = models.IntegerField(default=0)
    variant_b_clicks = models.IntegerField(default=0)
    variant_b_conversions = models.IntegerField(default=0)

    variant_c_sent = models.IntegerField(default=0)
    variant_c_opens = models.IntegerField(default=0)
    variant_c_clicks = models.IntegerField(default=0)

    variant_d_sent = models.IntegerField(default=0)
    variant_e_sent = models.IntegerField(default=0)

    # Winner
    winning_variant = models.CharField(max_length=1, blank=True, help_text="A, B, C, D, or E")
    is_statistically_significant = models.BooleanField(default=False)
    confidence_level = models.FloatField(default=0.0, help_text="Statistical confidence (0-100)")

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.campaign.name} - {self.test_element} test"


class DripCampaign(models.Model):
    """
    Automated email drip sequences
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]

    TRIGGER_TYPES = [
        ('lead_created', 'Lead Created'),
        ('contact_created', 'Contact Created'),
        ('deal_stage_changed', 'Deal Stage Changed'),
        ('tag_added', 'Tag Added'),
        ('form_submitted', 'Form Submitted'),
        ('date_based', 'Date-Based (Birthday, Anniversary)'),
        ('manual', 'Manual Enrollment'),
        ('webhook', 'Webhook Trigger'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='drip_campaigns')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    trigger_type = models.CharField(max_length=50, choices=TRIGGER_TYPES)
    trigger_config = models.JSONField(default=dict, help_text="Trigger-specific configuration")

    # Enrollment rules
    enrollment_conditions = models.JSONField(default=dict, help_text="Who can enter this drip")
    allow_re_enrollment = models.BooleanField(default=False)
    max_enrollments_per_contact = models.IntegerField(default=1)

    # Exit conditions
    exit_conditions = models.JSONField(default=list, help_text="Conditions to exit sequence")
    respect_unsubscribes = models.BooleanField(default=True)
    skip_weekends = models.BooleanField(default=False)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_active = models.BooleanField(default=False)

    # Stats
    total_enrolled = models.IntegerField(default=0)
    currently_enrolled = models.IntegerField(default=0)
    completed_count = models.IntegerField(default=0)
    exited_early_count = models.IntegerField(default=0)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.get_trigger_type_display()}"


class DripCampaignStep(models.Model):
    """
    Individual steps in a drip campaign sequence
    """
    drip_campaign = models.ForeignKey(DripCampaign, on_delete=models.CASCADE, related_name='steps')
    step_number = models.IntegerField(help_text="Order in sequence (1, 2, 3...)")
    name = models.CharField(max_length=200)

    # Delay from previous step
    delay_value = models.IntegerField(default=1)
    delay_unit = models.CharField(max_length=20, choices=[
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
    ], default='days')

    # Email to send
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True)
    subject_override = models.CharField(max_length=200, blank=True, help_text="Override template subject")

    # Conditional branching
    has_branch = models.BooleanField(default=False)
    branch_conditions = models.JSONField(default=dict, blank=True, help_text="If-then branching logic")

    # Stats
    sent_count = models.IntegerField(default=0)
    open_count = models.IntegerField(default=0)
    click_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['drip_campaign', 'step_number']
        unique_together = [['drip_campaign', 'step_number']]

    def __str__(self):
        return f"{self.drip_campaign.name} - Step {self.step_number}: {self.name}"


class DripCampaignEnrollment(models.Model):
    """
    Tracks individual contact/lead enrollment in drip campaigns
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('exited', 'Exited Early'),
        ('paused', 'Paused'),
    ]

    drip_campaign = models.ForeignKey(DripCampaign, on_delete=models.CASCADE, related_name='enrollments')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='drip_enrollments')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='drip_enrollments')

    current_step = models.ForeignKey(DripCampaignStep, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Timing
    enrolled_at = models.DateTimeField(auto_now_add=True)
    next_send_at = models.DateTimeField(help_text="When to send next email")
    completed_at = models.DateTimeField(null=True, blank=True)
    exited_at = models.DateTimeField(null=True, blank=True)
    exit_reason = models.CharField(max_length=200, blank=True)

    # Progress tracking
    steps_completed = models.IntegerField(default=0)
    total_opens = models.IntegerField(default=0)
    total_clicks = models.IntegerField(default=0)

    class Meta:
        ordering = ['-enrolled_at']
        indexes = [
            models.Index(fields=['status', 'next_send_at']),
            models.Index(fields=['drip_campaign', 'status']),
        ]

    def __str__(self):
        recipient = self.contact or self.lead
        return f"{recipient} in {self.drip_campaign.name}"


class EmailEngagement(models.Model):
    """
    Detailed engagement tracking per recipient
    """
    email = models.OneToOneField(Email, on_delete=models.CASCADE, related_name='engagement')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='email_engagements')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='email_engagements')

    # Open tracking
    opens_count = models.IntegerField(default=0)
    first_opened_at = models.DateTimeField(null=True, blank=True)
    last_opened_at = models.DateTimeField(null=True, blank=True)

    # Click tracking
    clicks_count = models.IntegerField(default=0)
    first_clicked_at = models.DateTimeField(null=True, blank=True)
    last_clicked_at = models.DateTimeField(null=True, blank=True)

    # Device & Location
    device_type = models.CharField(max_length=50, blank=True, help_text="desktop, mobile, tablet")
    email_client = models.CharField(max_length=100, blank=True, help_text="Gmail, Outlook, etc.")
    operating_system = models.CharField(max_length=100, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, blank=True)

    # User agent
    user_agent = models.TextField(blank=True)

    # Engagement score (0-100)
    engagement_score = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['contact', 'engagement_score']),
            models.Index(fields=['device_type']),
        ]

    def __str__(self):
        return f"Engagement for {self.email.to_email}"


class LinkClick(models.Model):
    """
    Individual link click tracking with UTM parameters
    """
    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='link_clicks')
    engagement = models.ForeignKey(EmailEngagement, on_delete=models.CASCADE, null=True, blank=True, related_name='clicks')

    # Link details
    url = models.URLField(max_length=1000)
    link_text = models.CharField(max_length=500, blank=True, help_text="Anchor text")
    link_position = models.IntegerField(default=0, help_text="Position in email (1st link, 2nd link, etc.)")

    # UTM tracking
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=200, blank=True)
    utm_content = models.CharField(max_length=200, blank=True)
    utm_term = models.CharField(max_length=200, blank=True)

    # Click metadata
    clicked_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    user_agent = models.TextField(blank=True)

    # Geolocation
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-clicked_at']
        indexes = [
            models.Index(fields=['email', 'url']),
            models.Index(fields=['clicked_at']),
        ]

    def __str__(self):
        return f"Click on {self.url[:50]} at {self.clicked_at}"


class UnsubscribePreference(models.Model):
    """
    Unsubscribe and email preference management
    """
    UNSUBSCRIBE_REASONS = [
        ('too_frequent', 'Emails too frequent'),
        ('not_relevant', 'Content not relevant'),
        ('never_subscribed', 'Never subscribed'),
        ('privacy_concerns', 'Privacy concerns'),
        ('other', 'Other'),
    ]

    FREQUENCY_PREFERENCES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('never', 'Never (Unsubscribed)'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='unsubscribe_preferences')
    contact = models.OneToOneField(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='unsubscribe_preference')
    lead = models.OneToOneField(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='unsubscribe_preference')

    # Global unsubscribe
    is_unsubscribed = models.BooleanField(default=False)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    unsubscribe_reason = models.CharField(max_length=50, choices=UNSUBSCRIBE_REASONS, blank=True)
    unsubscribe_reason_text = models.TextField(blank=True)

    # Campaign from which they unsubscribed
    unsubscribed_from_campaign = models.ForeignKey(EmailCampaign, on_delete=models.SET_NULL, null=True, blank=True)

    # Preference center
    frequency_preference = models.CharField(max_length=20, choices=FREQUENCY_PREFERENCES, default='weekly')
    campaign_type_preferences = models.JSONField(default=dict, help_text="Preferences per campaign type")

    # Resubscribe support
    resubscribe_token = models.CharField(max_length=100, unique=True, blank=True)
    resubscribed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['is_unsubscribed']),
        ]

    def __str__(self):
        recipient = self.contact or self.lead
        status = "Unsubscribed" if self.is_unsubscribed else "Subscribed"
        return f"{recipient} - {status}"


class CampaignGoal(models.Model):
    """
    Campaign performance goals and tracking
    """
    GOAL_TYPES = [
        ('open_rate', 'Open Rate'),
        ('click_rate', 'Click Rate'),
        ('click_to_open_rate', 'Click-to-Open Rate'),
        ('conversion_rate', 'Conversion Rate'),
        ('revenue', 'Revenue'),
        ('engagement_score', 'Engagement Score'),
    ]

    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, related_name='goals')
    goal_type = models.CharField(max_length=50, choices=GOAL_TYPES)
    target_value = models.FloatField(help_text="Target value to achieve")
    actual_value = models.FloatField(default=0.0, help_text="Current actual value")

    # Achievement tracking
    is_achieved = models.BooleanField(default=False)
    achieved_at = models.DateTimeField(null=True, blank=True)
    progress_percentage = models.FloatField(default=0.0, help_text="Progress towards goal (0-100%)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['campaign', 'goal_type']

    def __str__(self):
        return f"{self.campaign.name} - {self.get_goal_type_display()}: {self.target_value}"

    def update_progress(self):
        """Calculate progress percentage"""
        if self.target_value > 0:
            self.progress_percentage = min((self.actual_value / self.target_value) * 100, 100)
            self.is_achieved = self.actual_value >= self.target_value
            if self.is_achieved and not self.achieved_at:
                from django.utils import timezone
                self.achieved_at = timezone.now()
        self.save()


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
