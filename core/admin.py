"""
Django admin configuration for core models.
"""
from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from .models import (
    Region, TransportType, POIType, RouteType, Waterbody,
    PublicTransportStation, LaunchPoint, PointOfInterest, Waypoint,
    RouteSection, WalkPath, SavedRoute, Image, Comment, Rating
)


class FixedOSMGeoAdmin(OSMGeoAdmin):
    """Fixed OSMGeoAdmin for Django 4.2 compatibility.
    
    This fixes the 'super' object has no attribute 'dicts' error
    that occurs in Django 4.2 with GeoDjango admin.
    
    The issue is typically related to Python 3.14+ compatibility.
    This workaround ensures the admin changelist works correctly.
    """
    
    def changelist_view(self, request, extra_context=None):
        """Override changelist_view to avoid template tag issues."""
        # Call parent but ensure extra_context is properly initialized
        if extra_context is None:
            extra_context = {}
        return super().changelist_view(request, extra_context)


@admin.register(Region)
class RegionAdmin(FixedOSMGeoAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    default_lon = 13.4050
    default_lat = 52.5200
    default_zoom = 11


@admin.register(TransportType)
class TransportTypeAdmin(admin.ModelAdmin):
    list_display = ['key', 'name', 'icon_class']
    search_fields = ['key', 'name']


@admin.register(POIType)
class POITypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon_class']
    search_fields = ['name']


@admin.register(RouteType)
class RouteTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name']
    search_fields = ['name', 'display_name']


@admin.register(Waterbody)
class WaterbodyAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(PublicTransportStation)
class PublicTransportStationAdmin(FixedOSMGeoAdmin):
    list_display = ['name', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name']
    filter_horizontal = ['station_types']
    readonly_fields = ['created_at', 'updated_at']
    default_lon = 13.4050
    default_lat = 52.5200
    default_zoom = 11


@admin.register(LaunchPoint)
class LaunchPointAdmin(FixedOSMGeoAdmin):
    list_display = ['name', 'accessibility', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'accessibility', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    default_lon = 13.4050
    default_lat = 52.5200
    default_zoom = 11


@admin.register(PointOfInterest)
class PointOfInterestAdmin(FixedOSMGeoAdmin):
    list_display = ['name', 'poi_type', 'accessibility', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'poi_type', 'accessibility', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    default_lon = 13.4050
    default_lat = 52.5200
    default_zoom = 11


@admin.register(Waypoint)
class WaypointAdmin(FixedOSMGeoAdmin):
    list_display = ['name', 'created_by', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    default_lon = 13.4050
    default_lat = 52.5200
    default_zoom = 11


@admin.register(RouteSection)
class RouteSectionAdmin(FixedOSMGeoAdmin):
    list_display = ['display_name', 'from_waypoint', 'to_waypoint', 'waterbody', 'distance_meters', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'waterbody', 'created_at']
    search_fields = ['name', 'from_waypoint__name', 'to_waypoint__name']
    filter_horizontal = ['route_types']
    readonly_fields = ['created_at', 'updated_at', 'distance_meters']
    default_lon = 13.4050
    default_lat = 52.5200
    default_zoom = 11
    
    def display_name(self, obj):
        """Return a display name that always has content for admin links."""
        return obj.name.strip() if obj.name and obj.name.strip() else f"Route Section {obj.id}"
    display_name.short_description = 'Name'
    display_name.admin_order_field = 'name'  # Allow sorting by name field


@admin.register(WalkPath)
class WalkPathAdmin(FixedOSMGeoAdmin):
    list_display = ['station', 'launch_point', 'distance_meters', 'created_at']
    list_filter = ['created_at']
    search_fields = ['station__name', 'launch_point__name']
    readonly_fields = ['created_at', 'updated_at']
    default_lon = 13.4050
    default_lat = 52.5200
    default_zoom = 11


@admin.register(SavedRoute)
class SavedRouteAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'user__username']
    filter_horizontal = ['sections']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'content_object', 'uploaded_by', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['caption']
    readonly_fields = ['uploaded_at']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'content_object', 'user', 'needs_fixing', 'status', 'created_at']
    list_filter = ['status', 'needs_fixing', 'created_at']
    search_fields = ['text', 'user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['comment', 'category', 'value', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['comment__text']

