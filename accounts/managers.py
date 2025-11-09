from django.db import models
from django.contrib.auth.models import UserManager as BaseUserManager
from moldcrm.middleware.account_middleware import get_current_account

class AccountManager(BaseUserManager):
    def get_queryset(self):
        queryset = super().get_queryset()
        current_account = get_current_account()
        
        if current_account:
            return queryset.filter(account=current_account)
        return queryset.none()
    
    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD: username})
    
    # Add custom create_superuser for email-based authentication
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user