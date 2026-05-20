from django.db import models
from django.conf import settings


class LoadReading(models.Model):
    """Seeded historical data from real LCL smart meter CSV files."""
    user        = models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=models.CASCADE,
                    related_name='load_readings',
                    null=True, blank=True
                  )
    datetime    = models.DateTimeField(db_index=True)
    load_kwh    = models.FloatField()          # ← renamed from load_kw
    temperature = models.FloatField(default=0) # not in LCL data, kept for schema compatibility
    hour        = models.IntegerField()
    day_of_week = models.IntegerField()
    is_weekend  = models.BooleanField()
    month       = models.IntegerField()

    class Meta:
        ordering = ['datetime']

    def __str__(self):
        return f"{self.datetime} — {self.load_kwh:.4f} kWh"


class ForecastResult(models.Model):
    """Stores 24-hour prediction results per user."""
    user          = models.ForeignKey(
                      settings.AUTH_USER_MODEL,
                      on_delete=models.CASCADE,
                      related_name='forecasts'
                    )
    generated_at  = models.DateTimeField(auto_now_add=True)
    target_hour   = models.DateTimeField()
    predicted_kwh = models.FloatField()        # ← renamed from predicted_kw
    is_peak       = models.BooleanField(default=False)
    model_used    = models.CharField(max_length=50, default='Random Forest')

    class Meta:
        ordering = ['target_hour']

    def __str__(self):
        return f"{self.user.email} | {self.target_hour} | {self.predicted_kwh:.4f} kWh"