from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LogoutView, RegisterView, LoginView, ProfileView

urlpatterns = [
    path('register/',      RegisterView.as_view()),   # POST /api/auth/register/
    path('login/',         LoginView.as_view()),       # POST /api/auth/login/
    path('logout/',        LogoutView.as_view()),      # POST /api/auth/logout/
    path('token/refresh/', TokenRefreshView.as_view()),# POST /api/auth/token/refresh/
    path('profile/',       ProfileView.as_view()),     # GET/PUT /api/auth/profile/
]