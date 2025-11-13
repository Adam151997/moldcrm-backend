from django.db import models
from accounts.models import Account
from users.models import User

class PipelineStage(models.Model):
    """Custom pipeline stages for deals"""
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='pipeline_stages')
    name = models.CharField(max_length=100)  # Internal name (e.g., 'prospect')
    display_name = models.CharField(max_length=100)  # Display name (e.g., 'Prospect')
    color = models.CharField(max_length=20, default='blue')  # Color for UI (e.g., 'blue', 'green')
    is_closed = models.BooleanField(default=False)  # Whether this stage is a closed stage
    is_won = models.BooleanField(default=False)  # Whether this is a won stage (only for closed stages)
    order = models.IntegerField(default=0)  # Order in the pipeline
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ['account', 'name']

    def __str__(self):
        return f"{self.display_name} ({self.account.name})"

class Lead(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('unqualified', 'Unqualified'),
    ]
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    source = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    custom_data = models.JSONField(default=dict, blank=True)  # For custom field data
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_leads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Contact(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    lead = models.OneToOneField(Lead, on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=100, blank=True)
    title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)  # For department/division
    custom_data = models.JSONField(default=dict, blank=True)  # For custom field data
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Deal(models.Model):
    STAGE_CHOICES = [
        ('prospect', 'Prospect'),
        ('qualification', 'Qualification'),
        ('proposal', 'Proposal'),
        ('negotiation', 'Negotiation'),
        ('closed_won', 'Closed Won'),
        ('closed_lost', 'Closed Lost'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='deals')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='prospect')
    expected_close_date = models.DateField(null=True, blank=True)
    probability = models.IntegerField(default=0)
    custom_data = models.JSONField(default=dict, blank=True)  # For custom field data
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_deals')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# NEW MODELS - FOR FUTURE USE (NO MIGRATIONS NEEDED)
class Activity(models.Model):
    ACTIVITY_TYPES = [
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('note', 'Note'),
        ('task', 'Task'),
        ('other', 'Other'),
    ]
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_activity_type_display()}: {self.title}"

class Note(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    content = models.TextField()
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='notes_list')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='notes_list')
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, null=True, blank=True, related_name='notes_list')
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Note by {self.created_by.get_full_name()} on {self.created_at.date()}"