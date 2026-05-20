from rest_framework import serializers
from .models import ApplianceProfile, DRResult, PeakEvent


class ApplianceProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model  = ApplianceProfile
        fields = ['id', 'name', 'power_kw', 'duration_hrs',
                  'start_window', 'end_window', 'appliance_class']
        read_only_fields = ['id']

    def validate_power_kw(self, value):
        if value <= 0:
            raise serializers.ValidationError("Power must be greater than 0.")
        return value

    def validate_duration_hrs(self, value):
        if not (1 <= value <= 24):
            raise serializers.ValidationError("Duration must be between 1 and 24 hours.")
        return value


class DRResultSerializer(serializers.ModelSerializer):
    """Full detail — includes hourly JSON curves."""
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model  = DRResult
        fields = [
            'id', 'user_email', 'mac_address', 'reporting_date', 'generated_at',
            'original_cost_gbp', 'optimized_cost_gbp', 'cost_saving_gbp',
            'carbon_reduced_kg',
            'has_risk', 'risk_events', 'peak_threshold_kw', 'user_peak_load_kw',
            'congratulations_message', 'environmental_message', 'notification_text',
            'hourly_json',
        ]
        read_only_fields = fields


class DRSummarySerializer(serializers.ModelSerializer):
    """Lightweight — for history list cards, no heavy JSON."""
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model  = DRResult
        fields = [
            'id', 'user_email', 'mac_address', 'reporting_date', 'generated_at',
            'original_cost_gbp', 'optimized_cost_gbp', 'cost_saving_gbp',
            'carbon_reduced_kg', 'has_risk', 'risk_events',
            'congratulations_message', 'notification_text',
        ]
        read_only_fields = fields


class PeakEventSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PeakEvent
        fields = ['id', 'mac_address', 'detected_at', 'hour',
                  'load_kw', 'threshold_kw', 'severity', 'is_resolved']
        read_only_fields = ['id', 'detected_at']