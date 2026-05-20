import uuid
from django.db import models
from django.conf import settings


class Property(models.Model):
    """
    Represents a home, apartment, or building.
    One user owns it but multiple family members can access it.
    """

    class PropertyType(models.TextChoices):
        RESIDENTIAL  = 'residential',  'Residential'
        COMMERCIAL   = 'commercial',   'Commercial'
        INDUSTRIAL   = 'industrial',   'Industrial'
        APARTMENT    = 'apartment',    'Apartment'

    class TariffPlan(models.TextChoices):
        STANDARD     = 'standard',     'Standard Fixed Rate'
        TIME_OF_USE  = 'tou',          'Time of Use'
        PREPAID      = 'prepaid',      'Prepaid'
        NET_METERING = 'net_metering', 'Net Metering (Solar)'

    # Ownership
    owner        = models.ForeignKey(
                     settings.AUTH_USER_MODEL,
                     on_delete=models.CASCADE,
                     related_name='owned_properties'
                   )

    # Basic info
    name         = models.CharField(max_length=100)           # "My Home", "Office Block A"
    property_type = models.CharField(
                     max_length=20,
                     choices=PropertyType.choices,
                     default=PropertyType.RESIDENTIAL
                    )

    # Address
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city          = models.CharField(max_length=100)
    district      = models.CharField(max_length=100, blank=True)
    province      = models.CharField(max_length=100, blank=True)
    country       = models.CharField(max_length=100, default='Nepal')
    postal_code   = models.CharField(max_length=20, blank=True)

    # Government / utility identifiers
    govt_property_id  = models.CharField(
                          max_length=100, blank=True,
                          help_text='Government-issued property/house ID'
                        )
    utility_account_no = models.CharField(
                           max_length=100, blank=True,
                           help_text='Electricity utility account number'
                         )
    consumer_no       = models.CharField(
                          max_length=100, blank=True,
                          help_text='NEA or local utility consumer number'
                        )

    # Settings
    timezone     = models.CharField(max_length=50, default='Asia/Kathmandu')
    tariff_plan  = models.CharField(
                     max_length=20,
                     choices=TariffPlan.choices,
                     default=TariffPlan.STANDARD
                    )
    peak_rate    = models.FloatField(default=1.257, help_text='NPR per kWh during peak')
    flat_rate    = models.FloatField(default=0.787, help_text='NPR per kWh during flat')
    valley_rate  = models.FloatField(default=0.299, help_text='NPR per kWh during valley')

    # Metadata
    is_active    = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'properties'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.owner.email}"


class HomeMember(models.Model):
    """
    Gives another user access to a property they don't own.
    This solves the family member sharing problem.
    """

    class Role(models.TextChoices):
        ADMIN    = 'admin',    'Admin'      # can manage meter + members
        MEMBER   = 'member',   'Member'     # can view usage only
        READONLY = 'readonly', 'Read Only'  # view only, no actions

    property  = models.ForeignKey(
                  Property,
                  on_delete=models.CASCADE,
                  related_name='members'
                )
    user      = models.ForeignKey(
                  settings.AUTH_USER_MODEL,
                  on_delete=models.CASCADE,
                  related_name='home_memberships'
                )
    role      = models.CharField(
                  max_length=10,
                  choices=Role.choices,
                  default=Role.MEMBER
                )
    invited_by = models.ForeignKey(
                   settings.AUTH_USER_MODEL,
                   on_delete=models.SET_NULL,
                   null=True, blank=True,
                   related_name='sent_invitations'
                 )
    joined_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['property', 'user']   # one membership per user per property

    def __str__(self):
        return f"{self.user.email} → {self.property.name} ({self.role})"


class SmartMeter(models.Model):
    """
    A physical smart meter device linked to a property.
    One property can have multiple meters (solar + grid, main + sub-meter).
    """

    class MeterType(models.TextChoices):
        MAIN        = 'main',        'Main Grid Meter'
        SUB         = 'sub',         'Sub Meter'
        SOLAR       = 'solar',       'Solar Generation Meter'
        EV          = 'ev',          'EV Charging Meter'
        INDUSTRIAL  = 'industrial',  'Industrial Meter'

    property     = models.ForeignKey(
                     Property,
                     on_delete=models.CASCADE,
                     related_name='meters'
                   )

    # Physical device identification
    mac_address  = models.CharField(
                     max_length=17, unique=True,
                     help_text='Device MAC address e.g. AA:BB:CC:DD:EE:FF'
                   )
    serial_no    = models.CharField(max_length=100, blank=True)
    device_model = models.CharField(max_length=100, blank=True)

    # User-defined
    label        = models.CharField(
                     max_length=100,
                     help_text='e.g. "Main meter", "Solar panel meter"'
                   )
    meter_type   = models.CharField(
                     max_length=20,
                     choices=MeterType.choices,
                     default=MeterType.MAIN
                   )

    # Status
    is_active        = models.BooleanField(default=True)
    is_verified      = models.BooleanField(default=False)  # admin verified
    registered_at    = models.DateTimeField(auto_now_add=True)
    last_reading_at  = models.DateTimeField(null=True, blank=True)

    # Technical specs
    rated_capacity_kw = models.FloatField(
                          null=True, blank=True,
                          help_text='Max rated capacity in kW'
                        )
    phase             = models.CharField(
                          max_length=10,
                          choices=[('single', 'Single Phase'), ('three', 'Three Phase')],
                          default='single'
                        )

    class Meta:
        ordering = ['-registered_at']

    def __str__(self):
        return f"{self.label} ({self.mac_address}) — {self.property.name}"


class EnergyReading(models.Model):
    """
    One time-stamped reading from a smart meter.
    This is the raw data that feeds into forecasting and analytics.
    """
    meter            = models.ForeignKey(
                         SmartMeter,
                         on_delete=models.CASCADE,
                         related_name='readings'
                       )
    timestamp        = models.DateTimeField(db_index=True)
    consumption_kwh  = models.FloatField()
    voltage          = models.FloatField(null=True, blank=True)
    current_amps     = models.FloatField(null=True, blank=True)
    power_factor     = models.FloatField(null=True, blank=True)
    frequency_hz     = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        unique_together = ['meter', 'timestamp']

    def __str__(self):
        return f"{self.meter.label} | {self.timestamp} | {self.consumption_kwh} kWh"


class MeterAlert(models.Model):
    """
    Anomaly or alert raised for a meter — high usage, outage, etc.
    """

    class AlertType(models.TextChoices):
        HIGH_USAGE   = 'high_usage',   'High Usage'
        OUTAGE       = 'outage',       'Power Outage'
        TAMPER       = 'tamper',       'Tampering Detected'
        PEAK         = 'peak',         'Peak Demand Warning'
        LOW_VOLTAGE  = 'low_voltage',  'Low Voltage'

    class Severity(models.TextChoices):
        LOW      = 'low',      'Low'
        MEDIUM   = 'medium',   'Medium'
        HIGH     = 'high',     'High'
        CRITICAL = 'critical', 'Critical'

    meter      = models.ForeignKey(SmartMeter, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=AlertType.choices)
    severity   = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MEDIUM)
    message    = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.alert_type} — {self.meter.label} ({self.severity})"