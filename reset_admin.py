import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moldcrm.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Account

User = get_user_model()

print("Starting admin reset...")

# Delete everything
User._base_manager.all().delete()
Account._base_manager.all().delete()
print("✅ All users and accounts deleted")

# Create fresh account
account = Account._base_manager.create(
    name='MoldCRM Organization', 
    industry='Technology',
    website='https://moldcrm.com'
)
print(f"✅ Account created: {account.name}")

# Create fresh admin user
user = User._base_manager.create(
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

print('✅ ADMIN USER CREATED SUCCESSFULLY!')
print('=== LOGIN CREDENTIALS ===')
print('Email: admin@moldcrm.com')
print('Password: admin123')
print('=========================')