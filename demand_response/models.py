from django.db import models
from django.conf import settings


class ApplianceProfile(models.Model):
    """One appliance belonging to one user."""

    CLASS_CHOICES = [('IL', 'Inflexible'), ('SL', 'Shiftable'), ('AL', 'Adjustable')]

    user         = models.ForeignKey(settings.AUTH_USER_MODEL,
                                     on_delete=models.CASCADE,
                                     related_name='appliances')
    name         = models.CharField(max_length=100)
    power_kw     = models.FloatField()
    duration_hrs = models.IntegerField()
    start_window = models.IntegerField()   # earliest start hour (0-23)
    end_window   = models.IntegerField()   # latest end hour (0-23)
    appliance_class = models.CharField(max_length=2, choices=CLASS_CHOICES)

    def __str__(self):
        return f"{self.user.email} — {self.name}"


class DRResult(models.Model):
    """Stores one optimization run result per user."""
    user           = models.ForeignKey(settings.AUTH_USER_MODEL,
                                       on_delete=models.CASCADE,
                                       related_name='dr_results')
    generated_at   = models.DateTimeField(auto_now_add=True)
    baseline_cost  = models.FloatField()
    optimized_cost = models.FloatField()
    cost_saving    = models.FloatField()
    peak_reduction = models.FloatField()
    schedule_json  = models.JSONField()       # full schedule stored as JSON
    hourly_json    = models.JSONField()       # hourly baseline vs optimized

    def __str__(self):
        return f"{self.user.email} | {self.generated_at:%Y-%m-%d} | saved NPR {self.cost_saving:.2f}"