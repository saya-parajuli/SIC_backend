from rest_framework import serializers
from .models import LoadReading, ForecastResult


class LoadReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model  = LoadReading
        fields = ['datetime', 'load_kw', 'temperature', 'hour', 'is_weekend']


class ForecastResultSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ForecastResult
        fields = ['id', 'generated_at', 'target_hour', 'predicted_kw', 'is_peak', 'model_used']