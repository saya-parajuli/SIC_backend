from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status, generics
from .models import ApplianceProfile, DRResult
from .optimize import run_optimization
from .serializers import ApplianceProfileSerializer, DRResultSerializer, DRSummarySerializer


class OptimizeView(APIView):
    """POST /api/dr/optimize/ — run optimization for logged-in user."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            appliances = ApplianceProfile.objects.filter(user=request.user)
            result = run_optimization(appliances)

            # Save result to DB
            DRResult.objects.create(
                user           = request.user,
                baseline_cost  = result['baseline_cost'],
                optimized_cost = result['optimized_cost'],
                cost_saving    = result['cost_saving'],
                peak_reduction = result['peak_reduction'],
                schedule_json  = result['schedule'],
                hourly_json    = result['hourly'],
            )
            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class DRHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        results = DRResult.objects.filter(
            user=request.user
        ).order_by('-generated_at')[:10]

        serializer = DRSummarySerializer(results, many=True)
        return Response(serializer.data)



class ApplianceListView(generics.ListCreateAPIView):
    """GET/POST /api/dr/appliances/ — view and add appliances."""
    serializer_class   = ApplianceProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ApplianceProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ApplianceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/DELETE /api/dr/appliances/<id>/ — edit or remove an appliance."""
    serializer_class   = ApplianceProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ApplianceProfile.objects.filter(user=self.request.user)
    



# Add this new view for fetching one full result with schedule + hourly data
class DRResultDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            result = DRResult.objects.get(pk=pk, user=request.user)
            serializer = DRResultSerializer(result)
            return Response(serializer.data)
        except DRResult.DoesNotExist:
            return Response({'error': 'Not found.'}, status=404)