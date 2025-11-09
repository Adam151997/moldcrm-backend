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
    
    # Add the missing method for createsuperuser
    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD: username})