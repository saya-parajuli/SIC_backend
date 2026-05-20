from django.urls import path
from .views import (
    OptimizeView, DRHistoryView, DRResultDetailView,
    DRLatestView, PeakEventListView,
    ApplianceListView, ApplianceDetailView,
)

urlpatterns = [
    path('optimize/',             OptimizeView.as_view()),         # POST — run optimization  /api/dr/optimize/
    path('latest/',               DRLatestView.as_view()),          # GET  — today's results  /api/dr/latest/
    path('history/',              DRHistoryView.as_view()),         # GET  — past 30 results  /api/dr/history/
    path('results/<int:pk>/',     DRResultDetailView.as_view()),    # GET  — full detail      /api/dr/results/<pk>/
    path('alerts/',               PeakEventListView.as_view()),     # GET  — unresolved alerts /api/dr/alerts/
    path('alerts/<int:pk>/',      PeakEventListView.as_view()),     # PATCH — resolve alert    /api/dr/alerts/<pk>/
    path('appliances/',           ApplianceListView.as_view()),     # GET/POST                 /api/dr/appliances/
    path('appliances/<int:pk>/',  ApplianceDetailView.as_view()),   # GET/PUT/DELETE           /api/dr/appliances/<pk>/
]