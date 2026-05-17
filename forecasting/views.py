from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .ml.predict import predict_next_24_hours
from .models import ForecastResult, LoadReading
from .serializers import ForecastResultSerializer, LoadReadingSerializer


class ForecastView(APIView):
    """GET /api/forecast/predict/ — run forecast and return 24-hour prediction."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            result = predict_next_24_hours()
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ForecastHistoryView(APIView):
    """GET /api/forecast/history/ — return saved forecast results for this user."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        forecasts = ForecastResult.objects.filter(user=request.user)
        serializer = ForecastResultSerializer(forecasts, many=True)
        return Response(serializer.data)


class LoadDataView(APIView):
    """GET /api/forecast/readings/ — historical load data (admin sees all, user sees own)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role in ['admin', 'staff']:
            readings = LoadReading.objects.all()[:500]   # limit for performance
        else:
            readings = LoadReading.objects.filter(user=request.user)[:500]

        serializer = LoadReadingSerializer(readings, many=True)
        return Response(serializer.data)