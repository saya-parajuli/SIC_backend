from django.contrib import admin
from .models import LoadReading, ForecastResult


@admin.register(LoadReading)
class LoadReadingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'datetime',
        'load_kwh',
        'temperature',
        'hour',
        'day_of_week',
        'is_weekend',
        'month',
    )

    list_filter = (
        'is_weekend',
        'month',
        'day_of_week',
    )

    search_fields = (
        'user__email',
    )

    ordering = (
        '-datetime',
    )

    date_hierarchy = 'datetime'


@admin.register(ForecastResult)
class ForecastResultAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'target_hour',
        'predicted_kwh',
        'is_peak',
        'model_used',
        'generated_at',
    )

    list_filter = (
        'is_peak',
        'model_used',
        'generated_at',
    )

    search_fields = (
        'user__email',
        'model_used',
    )

    readonly_fields = (
        'generated_at',
    )

    ordering = (
        '-generated_at',
    )

    date_hierarchy = 'target_hour'