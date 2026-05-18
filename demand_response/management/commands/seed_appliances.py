from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from demand_response.models import ApplianceProfile

User = get_user_model()

DEFAULT_APPLIANCES = [
    ('LED Lights',      0.10, 5,  18, 23, 'AL'),
    ('Air Conditioner', 1.50, 6,  14, 22, 'AL'),
    ('Refrigerator',    0.15, 24,  0, 23, 'IL'),
    ('WiFi Router',     0.02, 24,  0, 23, 'IL'),
    ('Washing Machine', 0.50, 2,  10, 18, 'SL'),
    ('Rice Cooker',     0.70, 1,  12, 15, 'SL'),
    ('EV Charger',      3.30, 4,  22,  6, 'SL'),
    ('Water Pump',      0.75, 1,   5,  8, 'SL'),
]

class Command(BaseCommand):
    help = 'Seeds default appliances for all users with no appliances'

    def handle(self, *args, **kwargs):
        for user in User.objects.filter(appliances__isnull=True):
            for name, power, dur, sw, ew, cls in DEFAULT_APPLIANCES:
                ApplianceProfile.objects.create(
                    user=user, name=name, power_kw=power,
                    duration_hrs=dur, start_window=sw,
                    end_window=ew, appliance_class=cls
                )
            self.stdout.write(f"✓ Seeded appliances for {user.email}")