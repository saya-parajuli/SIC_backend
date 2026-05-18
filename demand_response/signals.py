from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import ApplianceProfile

User = get_user_model()

DEFAULT_APPLIANCES = [
    ('LED Lights',      0.10, 5,  18, 23, 'AL'),
    ('Air Conditioner', 1.50, 6,  14, 22, 'AL'),
    ('Electric Heater', 2.00, 3,  18, 22, 'AL'),
    ('Fan',             0.08, 10, 10, 20, 'AL'),
    ('Refrigerator',    0.15, 24,  0, 23, 'IL'),
    ('WiFi Router',     0.02, 24,  0, 23, 'IL'),
    ('Security System', 0.03, 24,  0, 23, 'IL'),
    ('Washing Machine', 0.50, 2,  10, 18, 'SL'),
    ('Rice Cooker',     0.70, 1,  12, 15, 'SL'),
    ('Dishwasher',      1.20, 1,  20, 23, 'SL'),
    ('EV Charger',      3.30, 4,  22,  6, 'SL'),
    ('Water Pump',      0.75, 1,   5,  8, 'SL'),
]


@receiver(post_save, sender=User)
def seed_appliances_for_new_user(sender, instance, created, **kwargs):
    """
    Fires when a new user registers.
    Seeds default appliances automatically — user never has to do anything.
    """
    if not created:
        return   # only run on first creation, not on profile updates

    # Avoid duplicates if signal fires twice
    if ApplianceProfile.objects.filter(user=instance).exists():
        return

    ApplianceProfile.objects.bulk_create([
        ApplianceProfile(
            user            = instance,
            name            = name,
            power_kw        = power,
            duration_hrs    = dur,
            start_window    = sw,
            end_window      = ew,
            appliance_class = cls,
        )
        for name, power, dur, sw, ew, cls in DEFAULT_APPLIANCES
    ])

    print(f"[Signal] Appliances seeded for new user: {instance.email}")