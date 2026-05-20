from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Property,
    HomeMember,
    SmartMeter,
    EnergyReading,
    MeterAlert
)


# ==========================================
# INLINE CONFIGURATIONS
# ==========================================

class HomeMemberInline(admin.TabularInline):
    model = HomeMember
    extra = 0


class SmartMeterInline(admin.TabularInline):
    model = SmartMeter
    extra = 0


# ==========================================
# PROPERTY ADMIN
# ==========================================

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'name',
        'owner',
        'property_type',
        'city',
        'tariff_plan',
        'is_active',
        'created_at',
    )

    list_filter = (
        'property_type',
        'tariff_plan',
        'is_active',
        'city',
        'country',
    )

    search_fields = (
        'name',
        'owner__email',
        'consumer_no',
        'utility_account_no',
        'govt_property_id',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    ordering = (
        '-created_at',
    )

    inlines = [
        HomeMemberInline,
        SmartMeterInline,
    ]


# ==========================================
# HOME MEMBER ADMIN
# ==========================================

@admin.register(HomeMember)
class HomeMemberAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'property',
        'role',
        'invited_by',
        'joined_at',
    )

    list_filter = (
        'role',
    )

    search_fields = (
        'user__email',
        'property__name',
    )

    readonly_fields = (
        'joined_at',
    )

    ordering = (
        '-joined_at',
    )


# ==========================================
# SMART METER ADMIN
# ==========================================

@admin.register(SmartMeter)
class SmartMeterAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'label',
        'property',
        'meter_type',
        'mac_address',
        'phase',
        'is_active',
        'verification_status',
        'registered_at',
    )

    list_filter = (
        'meter_type',
        'phase',
        'is_active',
        'is_verified',
    )

    search_fields = (
        'label',
        'mac_address',
        'serial_no',
        'property__name',
    )

    readonly_fields = (
        'registered_at',
        'last_reading_at',
    )

    ordering = (
        '-registered_at',
    )

    def verification_status(self, obj):

        if obj.is_verified:
            return format_html(
                '<span style="color:{}; font-weight:bold;">{}</span>',
                'green',
                'Verified'
            )

        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            'red',
            'Not Verified'
        )

    verification_status.short_description = "Verification"


# ==========================================
# ENERGY READING ADMIN
# ==========================================

@admin.register(EnergyReading)
class EnergyReadingAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'meter',
        'timestamp',
        'consumption_kwh',
        'voltage',
        'current_amps',
        'power_factor',
        'frequency_hz',
    )

    list_filter = (
        'meter__meter_type',
    )

    search_fields = (
        'meter__label',
        'meter__mac_address',
    )

    ordering = (
        '-timestamp',
    )

    date_hierarchy = 'timestamp'


# ==========================================
# METER ALERT ADMIN
# ==========================================

@admin.register(MeterAlert)
class MeterAlertAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'meter',
        'alert_type',
        'colored_severity',
        'is_resolved',
        'created_at',
    )

    list_filter = (
        'alert_type',
        'severity',
        'is_resolved',
    )

    search_fields = (
        'meter__label',
        'meter__mac_address',
        'message',
    )

    readonly_fields = (
        'created_at',
        'resolved_at',
    )

    ordering = (
        '-created_at',
    )

    def colored_severity(self, obj):

        colors = {
            'low': 'green',
            'medium': 'orange',
            'high': 'red',
            'critical': 'darkred',
        }

        return format_html(
            '<strong style="color:{};">{}</strong>',
            colors.get(obj.severity, 'black'),
            obj.severity.upper()
        )

    colored_severity.short_description = 'Severity'