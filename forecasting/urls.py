from django.urls import path
from .views import ForecastView, ForecastHistoryView, LoadDataView

urlpatterns = [
    path('predict/',  ForecastView.as_view()),       # GET /api/forecast/predict/
    path('history/',  ForecastHistoryView.as_view()), # GET /api/forecast/history/
    path('readings/', LoadDataView.as_view()),         # GET /api/forecast/readings/
]