from django.db import models
from django.conf import settings


class ApplianceProfile(models.Model):
    """
    Kept for user-defined appliance metadata.
    Classification is now used for display only —
    the optimizer works on the household load curve directly.
    """
    CLASS_CHOICES = [('IL', 'Inflexible'), ('SL', 'Shiftable'), ('AL', 'Adjustable')]

    user            = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appliances')
    name            = models.CharField(max_length=100)
    power_kw        = models.FloatField()
    duration_hrs    = models.IntegerField()
    start_window    = models.IntegerField()
    end_window      = models.IntegerField()
    appliance_class = models.CharField(max_length=2, choices=CLASS_CHOICES)

    def __str__(self):
        return f"{self.user.email} — {self.name}"


class DRResult(models.Model):
    """
    Stores one optimization run per smart meter (MAC address).
    Linked to a user through their registered SmartMeter.
    """
    PERIOD_CHOICES = [
        ('Peak',     'Peak'),
        ('Normal',   'Normal'),
        ('Off-Peak', 'Off-Peak'),
    ]

    user              = models.ForeignKey(
                          settings.AUTH_USER_MODEL,
                          on_delete=models.CASCADE,
                          related_name='dr_results'
                        )
    mac_address       = models.CharField(max_length=17, db_index=True)
    reporting_date    = models.DateField()
    generated_at      = models.DateTimeField(auto_now_add=True)

    # Cost metrics (GBP)
    original_cost_gbp  = models.FloatField()
    optimized_cost_gbp = models.FloatField()
    cost_saving_gbp    = models.FloatField()

    # Environmental
    carbon_reduced_kg  = models.FloatField()

    # Risk assessment
    has_risk           = models.BooleanField(default=False)
    risk_events        = models.IntegerField(default=0)
    peak_threshold_kw  = models.FloatField()
    user_peak_load_kw  = models.FloatField()

    # Reward messaging
    congratulations_message  = models.TextField(blank=True)
    environmental_message    = models.TextField(blank=True)
    notification_text        = models.TextField(blank=True)

    # Hourly load profiles stored as JSON
    hourly_json        = models.JSONField()   # hours, original_curve, optimised_curve

    class Meta:
        ordering = ['-generated_at']
        # One result per meter per date — no duplicates
        unique_together = ['mac_address', 'reporting_date']

    def __str__(self):
        return f"{self.mac_address} | {self.reporting_date} | saved £{self.cost_saving_gbp:.2f}"


class PeakEvent(models.Model):
    """
    Records individual peak demand events detected for a meter.
    Used for notification history and analytics.
    """
    SEVERITY_CHOICES = [
        ('low',      'Low'),
        ('medium',   'Medium'),
        ('high',     'High'),
        ('critical', 'Critical'),
    ]

    user          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='peak_events')
    mac_address   = models.CharField(max_length=17, db_index=True)
    detected_at   = models.DateTimeField(auto_now_add=True)
    hour          = models.IntegerField()
    load_kw       = models.FloatField()
    threshold_kw  = models.FloatField()
    severity      = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    is_resolved   = models.BooleanField(default=False)

    class Meta:
        ordering = ['-detected_at']

    def __str__(self):
        return f"{self.mac_address} | Hour {self.hour} | {self.load_kw:.2f} kW ({self.severity})"