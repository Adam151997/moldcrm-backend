# Generated migration file to remove Webhook and WebhookLog models

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0002_email_provider'),
    ]

    operations = [
        # Delete WebhookLog model (must be deleted first due to foreign key)
        migrations.DeleteModel(
            name='WebhookLog',
        ),

        # Delete Webhook model
        migrations.DeleteModel(
            name='Webhook',
        ),
    ]
