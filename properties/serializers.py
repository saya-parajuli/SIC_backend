from rest_framework import serializers
from .models import Property, HomeMember, SmartMeter, EnergyReading, MeterAlert


class PropertySerializer(serializers.ModelSerializer):
    owner_email  = serializers.CharField(source='owner.email', read_only=True)
    meter_count  = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()

    class Meta:
        model  = Property
        fields = [
            'id', 'owner_email', 'name', 'property_type',
            'address_line1', 'address_line2', 'city', 'district',
            'province', 'country', 'postal_code',
            'govt_property_id', 'utility_account_no', 'consumer_no',
            'timezone', 'tariff_plan',
            'peak_rate', 'flat_rate', 'valley_rate',
            'is_active', 'created_at', 'meter_count', 'member_count',
        ]
        read_only_fields = ['id', 'owner_email', 'created_at']

    def get_meter_count(self, obj):
        return obj.meters.filter(is_active=True).count()

    def get_member_count(self, obj):
        return obj.members.count()


class HomeMemberSerializer(serializers.ModelSerializer):
    user_email    = serializers.CharField(source='user.email', read_only=True)
    user_name     = serializers.CharField(source='user.full_name', read_only=True)
    property_name = serializers.CharField(source='property.name', read_only=True)
    invite_email  = serializers.EmailField(write_only=True, required=False)

    class Meta:
        model  = HomeMember
        fields = [
            'id', 'user_email', 'user_name', 'property_name',
            'role', 'joined_at', 'invite_email',
        ]
        read_only_fields = ['id', 'user_email', 'user_name', 'property_name', 'joined_at']

    def validate_invite_email(self, value):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email.")
        return value


class SmartMeterSerializer(serializers.ModelSerializer):
    property_name   = serializers.CharField(source='property.name', read_only=True)
    reading_count   = serializers.SerializerMethodField()

    class Meta:
        model  = SmartMeter
        fields = [
            'id', 'property', 'property_name',
            'mac_address', 'serial_no', 'device_model',
            'label', 'meter_type', 'phase', 'rated_capacity_kw',
            'is_active', 'is_verified',
            'registered_at', 'last_reading_at', 'reading_count',
        ]
        read_only_fields = ['id', 'is_verified', 'registered_at',
                            'last_reading_at', 'property_name']

    def get_reading_count(self, obj):
        return obj.readings.count()

    def validate_mac_address(self, value):
        import re
        pattern = r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "Invalid MAC address format. Use AA:BB:CC:DD:EE:FF"
            )
        return value.upper()

    def validate(self, data):
        # User can only add meter to their own property
        request = self.context.get('request')
        if request and 'property' in data:
            prop = data['property']
            from .permissions import get_user_property_access
            access = get_user_property_access(request.user, prop.id)
            if access not in ['owner', 'admin']:
                raise serializers.ValidationError(
                    "You can only add meters to properties you own."
                )
        return data


class EnergyReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model  = EnergyReading
        fields = [
            'id', 'meter', 'timestamp',
            'consumption_kwh', 'voltage', 'current_amps',
            'power_factor', 'frequency_hz',
        ]
        read_only_fields = ['id']


class MeterAlertSerializer(serializers.ModelSerializer):
    meter_label = serializers.CharField(source='meter.label', read_only=True)

    class Meta:
        model  = MeterAlert
        fields = [
            'id', 'meter', 'meter_label', 'alert_type',
            'severity', 'message', 'is_resolved',
            'created_at', 'resolved_at',
        ]
        read_only_fields = ['id', 'created_at']