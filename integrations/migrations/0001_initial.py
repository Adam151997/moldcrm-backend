from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0002_alter_account_managers'),
        ('crm', '0005_create_activity_note_tables'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('template_type', models.CharField(choices=[('welcome', 'Welcome Email'), ('follow_up', 'Follow-up'), ('proposal', 'Proposal'), ('thank_you', 'Thank You'), ('reminder', 'Reminder'), ('custom', 'Custom')], max_length=50)),
                ('subject', models.CharField(max_length=200)),
                ('body_html', models.TextField()),
                ('body_text', models.TextField(blank=True)),
                ('available_variables', models.JSONField(default=list)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_templates', to='accounts.account')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='EmailCampaign',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('scheduled', 'Scheduled'), ('sending', 'Sending'), ('completed', 'Completed'), ('paused', 'Paused')], default='draft', max_length=20)),
                ('recipient_filter', models.JSONField(default=dict)),
                ('scheduled_at', models.DateTimeField(blank=True, null=True)),
                ('total_recipients', models.IntegerField(default=0)),
                ('sent_count', models.IntegerField(default=0)),
                ('opened_count', models.IntegerField(default=0)),
                ('clicked_count', models.IntegerField(default=0)),
                ('bounced_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_campaigns', to='accounts.account')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('template', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='integrations.emailtemplate')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_email', models.EmailField(max_length=254)),
                ('to_email', models.EmailField(max_length=254)),
                ('subject', models.CharField(max_length=200)),
                ('body_html', models.TextField()),
                ('body_text', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('queued', 'Queued'), ('sent', 'Sent'), ('delivered', 'Delivered'), ('opened', 'Opened'), ('clicked', 'Clicked'), ('bounced', 'Bounced'), ('failed', 'Failed')], default='queued', max_length=20)),
                ('tracking_id', models.CharField(blank=True, max_length=100, unique=True)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('delivered_at', models.DateTimeField(blank=True, null=True)),
                ('opened_at', models.DateTimeField(blank=True, null=True)),
                ('clicked_at', models.DateTimeField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emails', to='accounts.account')),
                ('campaign', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='emails', to='integrations.emailcampaign')),
                ('contact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='emails', to='crm.contact')),
                ('deal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='emails', to='crm.deal')),
                ('lead', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='emails', to='crm.lead')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Webhook',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('url', models.URLField(max_length=500)),
                ('event_types', models.JSONField(default=list)),
                ('secret', models.CharField(blank=True, max_length=255)),
                ('headers', models.JSONField(default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('total_calls', models.IntegerField(default=0)),
                ('failed_calls', models.IntegerField(default=0)),
                ('last_called_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='webhooks', to='accounts.account')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='WebhookLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(max_length=50)),
                ('payload', models.JSONField()),
                ('response_code', models.IntegerField(null=True)),
                ('response_body', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('success', 'Success'), ('failed', 'Failed')], max_length=20)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('webhook', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='integrations.webhook')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ExternalIntegration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(choices=[('zapier', 'Zapier'), ('make', 'Make (Integromat)'), ('n8n', 'n8n'), ('custom_api', 'Custom API'), ('slack', 'Slack'), ('google_sheets', 'Google Sheets'), ('hubspot', 'HubSpot'), ('salesforce', 'Salesforce')], max_length=50)),
                ('name', models.CharField(max_length=200)),
                ('api_key', models.CharField(blank=True, max_length=500)),
                ('api_secret', models.CharField(blank=True, max_length=500)),
                ('access_token', models.CharField(blank=True, max_length=500)),
                ('refresh_token', models.CharField(blank=True, max_length=500)),
                ('config', models.JSONField(default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('last_sync_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='integrations', to='accounts.account')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
    ]
