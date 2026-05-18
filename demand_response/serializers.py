from rest_framework import serializers
from .models import ApplianceProfile, DRResult


class ApplianceProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model  = ApplianceProfile
        fields = [
            'id',
            'name',
            'power_kw',
            'duration_hrs',
            'start_window',
            'end_window',
            'appliance_class',
        ]
        read_only_fields = ['id']

    def validate_power_kw(self, value):
        if value <= 0:
            raise serializers.ValidationError("Power must be greater than 0.")
        return value

    def validate_duration_hrs(self, value):
        if not (1 <= value <= 24):
            raise serializers.ValidationError("Duration must be between 1 and 24 hours.")
        return value

    def validate_start_window(self, value):
        if not (0 <= value <= 23):
            raise serializers.ValidationError("Start window must be between 0 and 23.")
        return value

    def validate_end_window(self, value):
        if not (0 <= value <= 23):
            raise serializers.ValidationError("End window must be between 0 and 23.")
        return value

    def validate_appliance_class(self, value):
        if value not in ['IL', 'SL', 'AL']:
            raise serializers.ValidationError("Class must be IL, SL, or AL.")
        return value


class DRResultSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model  = DRResult
        fields = [
            'id',
            'user_email',
            'generated_at',
            'baseline_cost',
            'optimized_cost',
            'cost_saving',
            'peak_reduction',
            'schedule_json',
            'hourly_json',
        ]
        read_only_fields = fields   # DR results are never edited directly


class DRSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for history list — excludes heavy JSON fields."""
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model  = DRResult
        fields = [
            'id',
            'user_email',
            'generated_at',
            'baseline_cost',
            'optimized_cost',
            'cost_saving',
            'peak_reduction',
        ]
        read_only_fields = fields