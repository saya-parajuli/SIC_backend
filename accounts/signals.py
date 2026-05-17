from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(pre_save, sender=User)
def assign_role_based_on_flags(sender, instance, **kwargs):
    """
    Automatically assign roles based on is_superuser / is_staff flags.
    Runs BEFORE the user is saved — so role is always in sync.
    """

    if instance.is_superuser:
        instance.role = User.Role.ADMIN

    elif instance.is_staff and not instance.is_superuser:
        instance.role = User.Role.STAFF

    else:
        instance.role = User.Role.USER


@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    """
    Fires after a new user is saved.
    Good place to send welcome emails, create related profiles, etc.
    """
    if created:
        print(f"[Signal] New user created: {instance.email} | Role: {instance.role}")