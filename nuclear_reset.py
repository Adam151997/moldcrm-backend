import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moldcrm.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Account
from django.db import connection

User = get_user_model()

print("=== NUCLEAR RESET STARTING ===")

# Nuclear delete
with connection.cursor() as cursor:
    cursor.execute("DELETE FROM users_user;")
    cursor.execute("DELETE FROM accounts_account;")
    cursor.execute("DELETE FROM django_session;")

print("✅ Database tables cleared")

# Create account
account = Account.objects.create(
    name='MoldCRM Nuclear', 
    industry='Technology'
)

# Create user with BOTH email and username
user = User.objects.create(
    username='admin',
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

print('✅ NUCLEAR RESET COMPLETE!')
print('=== TEST THESE COMBINATIONS ===')
print('Option 1 - Username: admin / Password: admin123')
print('Option 2 - Email: admin@moldcrm.com / Password: admin123')
print('===============================')