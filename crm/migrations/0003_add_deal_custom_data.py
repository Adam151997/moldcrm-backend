# Generated manually to add missing custom_data field to Deal model
# This is needed because migration 0002 was already applied without this field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0002_add_custom_data_to_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='deal',
            name='custom_data',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
