from django.db import models
from moldcrm.middleware.account_middleware import get_current_account

class AccountManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        current_account = get_current_account()
        
        if current_account:
            return queryset.filter(account=current_account)
        return queryset.none()  # Safety: return empty if no account