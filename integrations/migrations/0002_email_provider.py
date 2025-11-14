# Generated migration file for EmailProvider model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('integrations', '0001_initial'),
    ]

    operations = [
        # Create EmailProvider model
        migrations.CreateModel(
            name='EmailProvider',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider_type', models.CharField(choices=[('sendgrid', 'SendGrid'), ('mailgun', 'Mailgun'), ('mailchimp', 'Mailchimp (Mandrill)'), ('brevo', 'Brevo (Sendinblue)'), ('klaviyo', 'Klaviyo')], max_length=50)),
                ('name', models.CharField(max_length=200)),
                ('api_key', models.CharField(blank=True, max_length=1000)),
                ('api_secret', models.CharField(blank=True, max_length=1000)),
                ('sender_email', models.EmailField(max_length=254)),
                ('sender_name', models.CharField(max_length=200)),
                ('config', models.JSONField(default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('daily_limit', models.IntegerField(default=0, help_text='0 means unlimited')),
                ('monthly_limit', models.IntegerField(default=0, help_text='0 means unlimited')),
                ('sent_today', models.IntegerField(default=0)),
                ('sent_this_month', models.IntegerField(default=0)),
                ('last_error', models.TextField(blank=True)),
                ('last_sent_at', models.DateTimeField(blank=True, null=True)),
                ('priority', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_providers', to='accounts.account')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['priority', 'name'],
            },
        ),

        # Add unique constraint
        migrations.AlterUniqueTogether(
            name='emailprovider',
            unique_together={('account', 'provider_type', 'sender_email')},
        ),

        # Add provider field to Email model
        migrations.AddField(
            model_name='email',
            name='provider',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='emails', to='integrations.emailprovider'),
        ),

        # Add provider_message_id field to Email model
        migrations.AddField(
            model_name='email',
            name='provider_message_id',
            field=models.CharField(blank=True, max_length=500),
        ),

        # Add providers ManyToMany field to EmailCampaign
        migrations.AddField(
            model_name='emailcampaign',
            name='providers',
            field=models.ManyToManyField(blank=True, related_name='campaigns', to='integrations.emailprovider'),
        ),

        # Add provider_strategy field to EmailCampaign
        migrations.AddField(
            model_name='emailcampaign',
            name='provider_strategy',
            field=models.CharField(choices=[('priority', 'Priority Order'), ('round_robin', 'Round Robin'), ('failover', 'Failover Only')], default='priority', max_length=20),
        ),
    ]
