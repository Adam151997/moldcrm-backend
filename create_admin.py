import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moldcrm.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Account

User = get_user_model()

# Create a default account first if it doesn't exist
default_account, created = Account.objects.get_or_create(
    name='Default Organization',
    industry='Technology',
    website='https://moldcrm.com'
)

if created:
    print("✅ Default account created")

# Create admin user if it doesn't exist
if not User.objects.filter(email='admin@moldcrm.com').exists():
    admin_user = User.objects.create_superuser(
        email='admin@moldcrm.com',
        password='Admin123!',
        first_name='Admin',
        last_name='User',
        account=default_account,
        role='admin'
    )
    print("✅ Admin user created: admin@moldcrm.com / Admin123!")
    print("✅ You can now login to the admin panel")
else:
    print("✅ Admin user already exists")