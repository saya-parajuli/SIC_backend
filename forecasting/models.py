from django.db import models
from django.conf import settings


class LoadReading(models.Model):
    """Stores the seeded historical data from her CSV."""
    user        = models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=models.CASCADE,
                    related_name='load_readings',
                    null=True, blank=True   # null = system-wide data, not per user yet
                  )
    datetime    = models.DateTimeField(db_index=True)
    load_kw     = models.FloatField()
    temperature = models.FloatField()
    hour        = models.IntegerField()
    day_of_week = models.IntegerField()
    is_weekend  = models.BooleanField()
    month       = models.IntegerField()

    class Meta:
        ordering = ['datetime']

    def __str__(self):
        return f"{self.datetime} — {self.load_kw:.2f} kW"


class ForecastResult(models.Model):
    """Stores 24-hour prediction results per user."""
    user          = models.ForeignKey(
                      settings.AUTH_USER_MODEL,
                      on_delete=models.CASCADE,
                      related_name='forecasts'
                    )
    generated_at  = models.DateTimeField(auto_now_add=True)
    target_hour   = models.DateTimeField()
    predicted_kw  = models.FloatField()
    is_peak       = models.BooleanField(default=False)
    model_used    = models.CharField(max_length=50)

    class Meta:
        ordering = ['target_hour']

    def __str__(self):
        return f"{self.user.email} | {self.target_hour} | {self.predicted_kw:.2f} kW"