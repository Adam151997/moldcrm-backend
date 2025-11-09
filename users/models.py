from django.contrib.auth.models import AbstractUser
from django.db import models
from accounts.models import Account
from accounts.managers import AccountManager

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

    # Fix the reverse accessor clash
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='user',
    )
    
    objects = AccountManager()
    
    def __str__(self):
        return self.email