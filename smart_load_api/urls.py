"""
URL configuration for smart_load_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from django.contrib.admin import site as admin_site
from .admin_views import admin_dashboard

# # Patch the admin site to use your custom index
# original_get_urls = admin_site.get_urls

# def custom_get_urls():
#     from django.urls import path
#     custom = [path('', admin_site.admin_view(admin_dashboard), name='index')]
#     return custom + original_get_urls()

# admin_site.get_urls = custom_get_urls

# # Override the default admin index with our custom dashboard
# admin.site.index_template = 'admin/index.html'

urlpatterns = [
    # path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/', admin.site.urls),

    path('api/auth/',      include('accounts.urls')),
    path('api/data/',      include('data_ingestion.urls')),
    path('api/forecast/',  include('forecasting.urls')),
    path('api/dr/',        include('demand_response.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/properties/', include('properties.urls')),
]