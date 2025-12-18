"""
API views for GeoJSON and REST endpoints.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.gis.geos import Point, LineString
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.contrib.contenttypes.models import ContentType

from .models import (
    Region, LaunchPoint, PointOfInterest, RouteSection, Waypoint,
    PublicTransportStation, WalkPath
)
from .serializers import (
    RegionSerializer,
    LaunchPointGeoJSONSerializer, PointOfInterestGeoJSONSerializer,
    RouteSectionGeoJSONSerializer, WaypointGeoJSONSerializer,
    PublicTransportStationGeoJSONSerializer, WalkPathGeoJSONSerializer,
    LaunchPointDetailSerializer, PointOfInterestDetailSerializer
)


def get_status_filter(user):
    """Get status filter based on user authentication."""
    if user.is_authenticated:
        return ['approved', 'pending']  # Show approved and pending for logged-in users
    else:
        return ['approved']  # Only approved for anonymous users


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Region model."""
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


class LaunchPointViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for LaunchPoint model."""
    queryset = LaunchPoint.objects.all()
    serializer_class = LaunchPointDetailSerializer

    def get_queryset(self):
        """Filter by status based on authentication."""
        queryset = LaunchPoint.objects.all()
        status_filter = get_status_filter(self.request.user)
        return queryset.filter(status__in=status_filter)

    @action(detail=False, methods=['get'])
    def geojson(self, request):
        """Return GeoJSON for all launch points."""
        queryset = self.get_queryset()
        serializer = LaunchPointGeoJSONSerializer(queryset, many=True)
        # GeoFeatureModelSerializer with many=True returns a FeatureCollection directly
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        """Return detailed information for a launch point."""
        launch_point = self.get_object()
        serializer = LaunchPointDetailSerializer(launch_point)
        return Response(serializer.data)


class PointOfInterestViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for PointOfInterest model."""
    queryset = PointOfInterest.objects.all()
    serializer_class = PointOfInterestDetailSerializer

    def get_queryset(self):
        """Filter by status based on authentication."""
        queryset = PointOfInterest.objects.all()
        status_filter = get_status_filter(self.request.user)
        return queryset.filter(status__in=status_filter)

    @action(detail=False, methods=['get'])
    def geojson(self, request):
        """Return GeoJSON for all POIs."""
        queryset = self.get_queryset()
        serializer = PointOfInterestGeoJSONSerializer(queryset, many=True)
        # GeoFeatureModelSerializer with many=True returns a FeatureCollection directly
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        """Return detailed information for a POI."""
        poi = self.get_object()
        serializer = PointOfInterestDetailSerializer(poi)
        return Response(serializer.data)


class RouteSectionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for RouteSection model."""
    queryset = RouteSection.objects.all()
    serializer_class = RouteSectionGeoJSONSerializer

    def get_queryset(self):
        """Filter by status based on authentication."""
        queryset = RouteSection.objects.all()
        status_filter = get_status_filter(self.request.user)
        return queryset.filter(status__in=status_filter)

    @action(detail=False, methods=['get'])
    def geojson(self, request):
        """Return GeoJSON for all route sections."""
        queryset = self.get_queryset()
        serializer = RouteSectionGeoJSONSerializer(queryset, many=True)
        # GeoFeatureModelSerializer with many=True returns a FeatureCollection directly
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def calculate_route(self, request):
        """Calculate route from selected sections."""
        # Debug: Print what we received
        print(f"calculate_route called. Request data: {request.data}")
        print(f"Request data type: {type(request.data)}")
        print(f"Request data keys: {request.data.keys() if hasattr(request.data, 'keys') else 'N/A'}")
        
        section_ids = request.data.get('section_ids', [])
        search_radius_meters = request.data.get('search_radius_meters', 500)
        
        print(f"Extracted section_ids: {section_ids}, type: {type(section_ids)}")
        print(f"Extracted search_radius_meters: {search_radius_meters}")

        if not section_ids:
            error_response = {
                'error': 'No section IDs provided',
                'received_data': dict(request.data) if hasattr(request.data, 'keys') else str(request.data),
                'section_ids_value': section_ids,
                'section_ids_type': str(type(section_ids))
            }
            print(f"Returning error: {error_response}")
            return Response(error_response, status=status.HTTP_400_BAD_REQUEST)
        
        # Ensure section_ids is a list
        if not isinstance(section_ids, list):
            error_response = {
                'error': 'section_ids must be a list',
                'received_data': dict(request.data) if hasattr(request.data, 'keys') else str(request.data),
                'section_ids_value': section_ids,
                'section_ids_type': str(type(section_ids))
            }
            print(f"Returning error: {error_response}")
            return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

        # Get selected sections
        sections = RouteSection.objects.filter(id__in=section_ids)
        if not sections.exists():
            return Response({'error': 'No sections found'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate total distance
        total_distance_m = sum(s.distance_meters for s in sections)

        # Collect waypoints
        waypoints = []
        for section in sections:
            if section.from_waypoint:
                waypoints.append(section.from_waypoint)
            if section.to_waypoint:
                waypoints.append(section.to_waypoint)
        # Remove duplicates
        waypoints = list(set(waypoints))

        # Find nearby launch points and POIs
        nearby_launch_points = []
        nearby_pois = []

        # Get status filter
        status_filter = get_status_filter(request.user)

        for section in sections:
            # Sample points along the route (every 100m or so)
            coords = section.route.coords
            sample_points = []
            for i in range(0, len(coords), max(1, len(coords) // 10)):  # Sample ~10 points per section
                sample_points.append(coords[i])

            for coord in sample_points:
                point = Point(coord[0], coord[1], srid=4326)

                # Find nearby launch points
                nearby_lps = LaunchPoint.objects.filter(
                    location__distance_lte=(point, D(m=search_radius_meters)),
                    status__in=status_filter
                ).annotate(
                    distance=Distance('location', point)
                ).order_by('distance')[:5]

                for lp in nearby_lps:
                    if lp.id not in [n['id'] for n in nearby_launch_points]:
                        nearby_launch_points.append({
                            'id': lp.id,
                            'name': lp.name,
                            'distance_meters': round(lp.distance.m, 0),
                            'nearest_section_id': section.id,
                            'accessibility': lp.accessibility
                        })

                # Find nearby POIs
                nearby_poi_list = PointOfInterest.objects.filter(
                    location__distance_lte=(point, D(m=search_radius_meters)),
                    status__in=status_filter
                ).annotate(
                    distance=Distance('location', point)
                ).order_by('distance')[:5]

                for poi in nearby_poi_list:
                    if poi.id not in [n['id'] for n in nearby_pois]:
                        nearby_pois.append({
                            'id': poi.id,
                            'name': poi.name,
                            'poi_type': poi.poi_type.name,
                            'distance_meters': round(poi.distance.m, 0),
                            'nearest_section_id': section.id
                        })

        # Serialize sections
        section_serializer = RouteSectionGeoJSONSerializer(sections, many=True)
        waypoint_serializer = WaypointGeoJSONSerializer(waypoints, many=True)

        return Response({
            'sections': [
                {
                    'id': s.id,
                    'name': s.name or f"Section {s.id}",
                    'distance_km': round(s.distance_meters / 1000.0, 2) if s.distance_meters else 0.0,
                    'from_waypoint': s.from_waypoint.name if s.from_waypoint else None,
                    'to_waypoint': s.to_waypoint.name if s.to_waypoint else None,
                }
                for s in sections
            ],
            'waypoints': [
                {
                    'id': w.id,
                    'name': w.name or f"Waypoint {w.id}",
                }
                for w in waypoints
            ],
            'total_distance_km': round(total_distance_m / 1000.0, 2),
            'nearby_launch_points': nearby_launch_points,
            'nearby_pois': nearby_pois,
            'search_radius_meters': search_radius_meters
        })


class WaypointViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Waypoint model."""
    queryset = Waypoint.objects.all()
    serializer_class = WaypointGeoJSONSerializer

    @action(detail=False, methods=['get'])
    def geojson(self, request):
        """Return GeoJSON for all waypoints."""
        queryset = self.get_queryset()
        serializer = WaypointGeoJSONSerializer(queryset, many=True)
        # GeoFeatureModelSerializer with many=True returns a FeatureCollection directly
        return Response(serializer.data)


class PublicTransportStationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for PublicTransportStation model."""
    queryset = PublicTransportStation.objects.all()
    serializer_class = PublicTransportStationGeoJSONSerializer

    def get_queryset(self):
        """Filter by status based on authentication."""
        queryset = PublicTransportStation.objects.all()
        status_filter = get_status_filter(self.request.user)
        return queryset.filter(status__in=status_filter)

    @action(detail=False, methods=['get'])
    def geojson(self, request):
        """Return GeoJSON for all stations."""
        queryset = self.get_queryset()
        serializer = PublicTransportStationGeoJSONSerializer(queryset, many=True)
        # GeoFeatureModelSerializer with many=True returns a FeatureCollection directly
        return Response(serializer.data)


class WalkPathViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for WalkPath model."""
    queryset = WalkPath.objects.all()
    serializer_class = WalkPathGeoJSONSerializer

    @action(detail=False, methods=['get'])
    def geojson(self, request):
        """Return GeoJSON for all walk paths."""
        queryset = self.get_queryset()
        serializer = WalkPathGeoJSONSerializer(queryset, many=True)
        # GeoFeatureModelSerializer with many=True returns a FeatureCollection directly
        return Response(serializer.data)

