from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def initialize_new_user(sender, instance, created, **kwargs):
    """
    Fires when a new user registers.
    Optimization now runs on-demand via API when the user has meters linked.
    Appliance seeding is optional — users can add appliances manually.
    """
    if not created:
        return

    print(f"[Signal] New user initialized: {instance.email} | Role: {instance.role}")
    # Optimization will be triggered by React on first dashboard load
    # via POST /api/dr/optimize/ once the user has linked a smart meter