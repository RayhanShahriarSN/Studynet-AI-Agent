# models.py
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.conf import settings
import secrets

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        """
        Creates and saves a User with the given username, email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a username')

        user = self.model(
            username=username,
            email=self.normalize_email(email),
        )
        user.set_password(password)
        # Generate bearer token ONLY during registration
        user.bearer_token = secrets.token_urlsafe(32)
        user.is_logged_in = False  # User not logged in yet
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        """
        Creates and saves a superuser with the given username, email and password.
        """
        user = self.create_user(
            username=username,
            email=email,
            password=password
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(verbose_name='Email', max_length=255, unique=True)
    tokens_used = models.PositiveIntegerField(default=0)
    bearer_token = models.CharField(max_length=100, unique=True, blank=True, null=True)
    is_logged_in = models.BooleanField(default=False)  # Track login status
    
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin
    
    def login_user(self):
        """Mark user as logged in"""
        self.is_logged_in = True
        self.save()
    
    def logout_user(self):
        """Mark user as logged out"""
        self.is_logged_in = False
        self.save()
    
    def regenerate_bearer_token(self):
        """Regenerate a new bearer token (admin only)"""
        self.bearer_token = secrets.token_urlsafe(32)
        self.is_logged_in = False  # Force re-login
        self.save()
        return self.bearer_token