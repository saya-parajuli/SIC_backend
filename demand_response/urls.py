from django.urls import path
from .views import OptimizeView, DRHistoryView, DRResultDetailView, ApplianceListView, ApplianceDetailView

urlpatterns = [
    path('optimize/',             OptimizeView.as_view()),        # POST /api/dr/optimize/
    path('history/',              DRHistoryView.as_view()),        # GET  /api/dr/history/
    path('results/<int:pk>/',     DRResultDetailView.as_view()),   # GET one full result  /api/dr/results/<id>/
    path('appliances/',           ApplianceListView.as_view()),    # GET / POST /api/dr/appliances/
    path('appliances/<int:pk>/',  ApplianceDetailView.as_view()),  # GET / PUT / DELETE  /api/dr/appliances/<id>/
]