"""
Views for core app.
"""
from django.shortcuts import render
from .models import Region


def map_view(request):
    """Main map view."""
    # Get all regions for navigation
    regions = Region.objects.all()
    context = {
        'regions': regions
    }
    return render(request, 'map.html', context)

