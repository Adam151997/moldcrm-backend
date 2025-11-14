from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0002_alter_account_managers'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('template_type', models.CharField(choices=[('saas', 'SaaS'), ('real_estate', 'Real Estate'), ('ecommerce', 'E-commerce'), ('consulting', 'Consulting'), ('agency', 'Agency'), ('custom', 'Custom')], max_length=20)),
                ('description', models.TextField()),
                ('icon', models.CharField(default='📋', max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('pipeline_stages', models.JSONField(default=list)),
                ('custom_fields', models.JSONField(default=list)),
                ('automation_rules', models.JSONField(default=list)),
                ('email_templates', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='AppliedTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('applied_at', models.DateTimeField(auto_now_add=True)),
                ('configuration', models.JSONField(default=dict)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applied_templates', to='accounts.account')),
                ('applied_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='templates.businesstemplate')),
            ],
            options={
                'ordering': ['-applied_at'],
            },
        ),
    ]
