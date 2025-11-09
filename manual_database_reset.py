import os
import django
import psycopg2
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moldcrm.settings')
django.setup()

print("=== MANUAL DATABASE RESET ===")

# Get database URL from environment
database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:LTUuBazqwpjrYvMRFBRjsnWxzfXhDwsA@maglev.proxy.rlwy.net:40335/railway')

# Parse database URL
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://')

print(f"Connecting to database...")

# Connect directly with psycopg2
conn = psycopg2.connect(database_url)
conn.autocommit = True
cursor = conn.cursor()

# Drop ALL tables in public schema
cursor.execute("""
    DO $$ DECLARE
        r RECORD;
    BEGIN
        FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
            EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
        END LOOP;
    END $$;
""")
print("✅ All tables dropped")

# Drop ALL sequences
cursor.execute("""
    DO $$ DECLARE
        r RECORD;
    BEGIN
        FOR r IN (SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public') LOOP
            EXECUTE 'DROP SEQUENCE IF EXISTS ' || quote_ident(r.sequence_name) || ' CASCADE';
        END LOOP;
    END $$;
""")
print("✅ All sequences dropped")

cursor.close()
conn.close()

print("✅ Database completely reset")

# Now run Django migrations
print("Running Django migrations...")
os.system('python manage.py makemigrations')
os.system('python manage.py migrate')

print("✅ Migrations completed")

# Create admin user
from django.contrib.auth import get_user_model
from accounts.models import Account

User = get_user_model()
Account = Account

# Create account
account = Account.objects.create(
    name='MoldCRM Fresh Start', 
    industry='Technology'
)
print("✅ Account created")

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

print('✅ MANUAL DATABASE RESET COMPLETE!')
print('=== FRESH START READY ===')
print('Email: admin@moldcrm.com')
print('Password: admin123')
print('=========================')