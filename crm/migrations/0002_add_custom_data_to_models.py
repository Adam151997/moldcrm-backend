# Generated manually for custom_data fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='custom_data',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='contact',
            name='custom_data',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='contact',
            name='department',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
