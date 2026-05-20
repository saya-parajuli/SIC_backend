from django.contrib import admin
from .models import ApplianceProfile, DRResult, PeakEvent


@admin.register(ApplianceProfile)
class ApplianceProfileAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'name',
        'power_kw',
        'duration_hrs',
        'appliance_class'
    )

    list_filter = (
        'appliance_class',
    )

    search_fields = (
        'name',
        'user__email',
    )


# @admin.register(DRResult)
# class DRResultAdmin(admin.ModelAdmin):
#     list_display = (
#         'id',
#         'user',
#         'mac_address',
#         'reporting_date',
#         'original_cost_gbp',
#         'optimized_cost_gbp',
#         'cost_saving_gbp',
#         'carbon_reduced_kg',
#         'has_risk',
#         'risk_events',
#         'generated_at',
#     )

#     list_filter = (
#         'has_risk',
#         'reporting_date',
#         'generated_at',
#     )

#     search_fields = (
#         'mac_address',
#         'user__email',
#     )

#     readonly_fields = (
#         'generated_at',
#     )

#     ordering = (
#         '-generated_at',
#     )


# @admin.register(PeakEvent)
# class PeakEventAdmin(admin.ModelAdmin):
#     list_display = (
#         'id',
#         'user',
#         'mac_address',
#         'hour',
#         'load_kw',
#         'threshold_kw',
#         'severity',
#         'is_resolved',
#         'detected_at',
#     )

#     list_filter = (
#         'severity',
#         'is_resolved',
#     )

#     search_fields = (
#         'mac_address',
#         'user__email',
#     )

#     readonly_fields = (
#         'detected_at',
#     )

#     ordering = (
#         '-detected_at',
#     )