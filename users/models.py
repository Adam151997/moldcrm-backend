from django.contrib.auth.models import AbstractUser
from django.db import models
from accounts.models import Account

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('rep', 'Sales/Marketing Rep'),
    ]
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='users')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='rep')
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    
    # Email-based authentication
    username = None
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []