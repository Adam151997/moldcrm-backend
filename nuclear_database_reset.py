import os
import django
import subprocess
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moldcrm.settings')
django.setup()

from django.db import connection

print("=== NUCLEAR DATABASE RESET ===")

# Drop all tables and start fresh
with connection.cursor() as cursor:
    # Get all table names
    cursor.execute("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
    """)
    tables = cursor.fetchall()
    
    # Drop all tables
    for table in tables:
        table_name = table[0]
        if table_name.startswith('django_') or table_name in ['accounts_account', 'users_user', 'crm_lead', 'crm_contact', 'crm_deal', 'custom_objects_customobject', 'custom_objects_customfield', 'custom_objects_customobjectrecord']:
            print(f"Dropping table: {table_name}")
            cursor.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')

print("✅ All tables dropped")

# Run migrations to recreate schema
print("Running migrations...")
subprocess.run([sys.executable, 'manage.py', 'makemigrations'])
subprocess.run([sys.executable, 'manage.py', 'migrate'])

print("✅ Database schema recreated")

# Now create admin user
from django.contrib.auth import get_user_model
from accounts.models import Account

User = get_user_model()

# Create account
account = Account.objects.create(
    name='MoldCRM Fresh Start', 
    industry='Technology'
)

# Create admin user
user = User.objects.create(
    email='admin@moldcrm.com', 
    first_name='Admin', 
    last_name='User', 
    account=account, 
    is_staff=True, 
    is_superuser=True,
    is_active=True
)
user.set_password('admin123')
user.save()

print('✅ NUCLEAR DATABASE RESET COMPLETE!')
print('=== FRESH START READY ===')
print('Email: admin@moldcrm.com')
print('Password: admin123')
print('=========================')