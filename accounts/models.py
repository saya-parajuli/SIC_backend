from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        ADMIN  = 'admin',  'Admin'
        STAFF  = 'staff',  'Staff'
        USER   = 'user',   'Normal User'

    email        = models.EmailField(unique=True)
    first_name   = models.CharField(max_length=50)
    last_name    = models.CharField(max_length=50)
    role         = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    organization = models.CharField(max_length=100, blank=True)
    phone        = models.CharField(max_length=20, blank=True)
    is_active    = models.BooleanField(default=True)
    is_staff     = models.BooleanField(default=False)
    date_joined  = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD  = 'email'       # login with email, not username
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_normal_user(self):
        return self.role == self.Role.USER