from datetime import date
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ApplianceProfile, DRResult, PeakEvent
from .serializers import (ApplianceProfileSerializer, DRResultSerializer,
                           DRSummarySerializer, PeakEventSerializer)
from .optimizer import run_optimization_for_user, run_optimization_for_meter


class OptimizeView(APIView):
    """
    POST /api/dr/optimize/
    Runs LP optimization for all active meters of the logged-in user.
    Saves results to DRResult, creates PeakEvent records if risks detected.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            results = run_optimization_for_user(request.user)

            if not results:
                return Response(
                    {'error': 'No active meters found or insufficient data.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            saved = []
            for r in results:
                if 'error' in r:
                    saved.append(r)
                    continue

                # Save or update result for today
                dr_result, created = DRResult.objects.update_or_create(
                    mac_address    = r['mac_address'],
                    reporting_date = date.today(),
                    defaults={
                        'user':                     request.user,
                        'original_cost_gbp':        r['original_cost_gbp'],
                        'optimized_cost_gbp':       r['optimized_cost_gbp'],
                        'cost_saving_gbp':          r['cost_saving_gbp'],
                        'carbon_reduced_kg':        r['carbon_reduced_kg'],
                        'has_risk':                 r['has_risk'],
                        'risk_events':              r['risk_events'],
                        'peak_threshold_kw':        r['peak_threshold_kw'],
                        'user_peak_load_kw':        r['user_peak_load_kw'],
                        'congratulations_message':  r['congratulations_message'],
                        'environmental_message':    r['environmental_message'],
                        'notification_text':        r['notification_text'],
                        'hourly_json':              r['hourly_json'],
                    }
                )

                # Create PeakEvent if risk detected
                if r['has_risk']:
                    PeakEvent.objects.get_or_create(
                        mac_address  = r['mac_address'],
                        detected_at__date = date.today(),
                        defaults={
                            'user':         request.user,
                            'hour':         r['hourly_json']['original_curve_kwh'].index(
                                              max(r['hourly_json']['original_curve_kwh'])
                                            ),
                            'load_kw':      r['user_peak_load_kw'],
                            'threshold_kw': r['peak_threshold_kw'],
                            'severity':     r['severity'],
                        }
                    )

                serializer = DRResultSerializer(dr_result)
                saved.append(serializer.data)

            return Response({'results': saved}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DRHistoryView(APIView):
    """GET /api/dr/history/ — past optimization summaries for this user."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = DRResult.objects.filter(user=request.user).order_by('-generated_at')[:30]
        serializer = DRSummarySerializer(qs, many=True)
        return Response(serializer.data)


class DRResultDetailView(APIView):
    """GET /api/dr/results/<pk>/ — full result including hourly curves."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            result = DRResult.objects.get(pk=pk, user=request.user)
            return Response(DRResultSerializer(result).data)
        except DRResult.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)


class DRLatestView(APIView):
    """
    GET /api/dr/latest/
    Returns today's optimization result for each of the user's meters.
    This is what the dashboard loads on first visit.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today   = date.today()
        results = DRResult.objects.filter(user=request.user, reporting_date=today)

        if not results.exists():
            return Response(
                {'message': 'No optimization run for today yet. POST to /api/dr/optimize/.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(DRResultSerializer(results, many=True).data)


class PeakEventListView(APIView):
    """GET /api/dr/alerts/ — peak events for this user's meters."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        events = PeakEvent.objects.filter(
            user=request.user, is_resolved=False
        ).order_by('-detected_at')[:20]
        return Response(PeakEventSerializer(events, many=True).data)

    def patch(self, request, pk):
        """Mark a peak event as resolved."""
        try:
            event = PeakEvent.objects.get(pk=pk, user=request.user)
            event.is_resolved = True
            event.save()
            return Response({'message': 'Alert resolved.'})
        except PeakEvent.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)


class ApplianceListView(generics.ListCreateAPIView):
    """GET/POST /api/dr/appliances/"""
    serializer_class   = ApplianceProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ApplianceProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ApplianceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/DELETE /api/dr/appliances/<id>/"""
    serializer_class   = ApplianceProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ApplianceProfile.objects.filter(user=self.request.user)