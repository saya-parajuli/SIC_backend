from django.urls import path
from .views import (PropertyListCreateView, PropertyDetailView,
                    HomeMemberView, SmartMeterListCreateView,
                    SmartMeterDetailView, OnboardingStatusView)

from django.db import models

urlpatterns = [
    path('',                    PropertyListCreateView.as_view()),  # GET/POST /api/properties/
    path('<int:pk>/',            PropertyDetailView.as_view()),      # GET/PUT/DELETE  /api/properties/<id>/
    path('<int:property_id>/members/', HomeMemberView.as_view()),   # GET/POST/DELETE members  /api/properties/<id>/members/
    path('meters/',             SmartMeterListCreateView.as_view()), # GET/POST meters  /api/properties/meters/
    path('meters/<int:pk>/',    SmartMeterDetailView.as_view()),     # GET/PUT/DELETE meter  /api/properties/meters/<id>/
    path('onboarding/',         OnboardingStatusView.as_view()),     # GET onboarding step  /api/properties/onboarding/
]