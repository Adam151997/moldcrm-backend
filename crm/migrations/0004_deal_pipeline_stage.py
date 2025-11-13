# Generated manually to add pipeline_stage field to Deal model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0003_create_pipelinestage_table'),
    ]

    operations = [
        migrations.AddField(
            model_name='deal',
            name='pipeline_stage',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='deals',
                to='crm.pipelinestage'
            ),
        ),
    ]
