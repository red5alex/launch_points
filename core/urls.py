"""
URL configuration for core app.
"""
from django.urls import path, include
from . import views

app_name = 'core'

urlpatterns = [
    # Main map view
    path('', views.map_view, name='map'),
    # Note: API endpoints are in main urls.py to avoid language prefix
]

