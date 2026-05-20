from django.urls import path
from .views import (PropertyListCreateView, PropertyDetailView,
                    HomeMemberView, SmartMeterListCreateView,
                    SmartMeterDetailView, OnboardingStatusView)

from django.db import models

urlpatterns = [
    path('',                    PropertyListCreateView.as_view()),  # GET/POST /api/properties/
    path('<int:pk>/',            PropertyDetailView.as_view()),      # GET/PUT/DELETE
    path('<int:property_id>/members/', HomeMemberView.as_view()),   # GET/POST/DELETE members
    path('meters/',             SmartMeterListCreateView.as_view()), # GET/POST meters
    path('meters/<int:pk>/',    SmartMeterDetailView.as_view()),     # GET/PUT/DELETE meter
    path('onboarding/',         OnboardingStatusView.as_view()),     # GET onboarding step
]