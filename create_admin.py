import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moldcrm.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Create admin user if it doesn't exist
if not User.objects.filter(email='admin@moldcrm.com').exists():
    User.objects.create_superuser(
        email='admin@moldcrm.com',
        password='Admin123!',
        first_name='Admin',
        last_name='User'
    )
    print("✅ Admin user created: admin@moldcrm.com / Admin123!")
else:
    print("✅ Admin user already exists")