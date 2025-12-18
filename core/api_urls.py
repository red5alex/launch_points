"""
API URL configuration.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    RegionViewSet, LaunchPointViewSet, PointOfInterestViewSet,
    RouteSectionViewSet, WaypointViewSet, PublicTransportStationViewSet,
    WalkPathViewSet
)

router = DefaultRouter()
router.register(r'regions', RegionViewSet, basename='region')
router.register(r'launch-points', LaunchPointViewSet, basename='launch-point')
router.register(r'pois', PointOfInterestViewSet, basename='poi')
router.register(r'route-sections', RouteSectionViewSet, basename='route-section')
router.register(r'waypoints', WaypointViewSet, basename='waypoint')
router.register(r'stations', PublicTransportStationViewSet, basename='station')
router.register(r'walk-paths', WalkPathViewSet, basename='walk-path')

urlpatterns = [
    path('', include(router.urls)),
    # Convenience endpoints with simpler names
    path('launch-points/geojson/', LaunchPointViewSet.as_view({'get': 'geojson'}), name='launch-points-geojson'),
    path('pois/geojson/', PointOfInterestViewSet.as_view({'get': 'geojson'}), name='pois-geojson'),
    path('route-sections/geojson/', RouteSectionViewSet.as_view({'get': 'geojson'}), name='route-sections-geojson'),
    path('waypoints/geojson/', WaypointViewSet.as_view({'get': 'geojson'}), name='waypoints-geojson'),
    path('stations/geojson/', PublicTransportStationViewSet.as_view({'get': 'geojson'}), name='stations-geojson'),
    path('walk-paths/geojson/', WalkPathViewSet.as_view({'get': 'geojson'}), name='walk-paths-geojson'),
    path('calculate-route/', RouteSectionViewSet.as_view({'post': 'calculate_route'}), name='calculate-route'),
    path('launch-point/<int:pk>/', LaunchPointViewSet.as_view({'get': 'detail'}), name='launch-point-detail'),
    path('poi/<int:pk>/', PointOfInterestViewSet.as_view({'get': 'detail'}), name='poi-detail'),
]

