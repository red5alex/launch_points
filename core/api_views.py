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
    
    def get_serializer_class(self):
        """Use detail serializer for retrieve, GeoJSON for list."""
        if self.action == 'retrieve' or self.action == 'detail':
            return LaunchPointDetailSerializer
        elif self.action == 'geojson':
            return LaunchPointGeoJSONSerializer
        return LaunchPointDetailSerializer

    @action(detail=False, methods=['get'])
    def geojson(self, request):
        """Return GeoJSON for all launch points."""
        queryset = self.get_queryset()
        serializer = LaunchPointGeoJSONSerializer(queryset, many=True)
        # GeoFeatureModelSerializer with many=True returns a FeatureCollection directly
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Return detailed information for a launch point."""
        try:
            instance = self.get_object()
            serializer = LaunchPointDetailSerializer(instance)
            return Response(serializer.data)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in launch point detail view: {e}", exc_info=True)
            from rest_framework import status as http_status
            return Response(
                {'error': str(e)},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        """Alias for retrieve using detail serializer."""
        return self.retrieve(request, pk=pk)


class PointOfInterestViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for PointOfInterest model."""
    queryset = PointOfInterest.objects.all()
    serializer_class = PointOfInterestDetailSerializer

    def get_queryset(self):
        """Filter by status based on authentication."""
        queryset = PointOfInterest.objects.all()
        status_filter = get_status_filter(self.request.user)
        return queryset.filter(status__in=status_filter)
    
    def get_serializer_class(self):
        """Use detail serializer for retrieve, GeoJSON for list."""
        if self.action == 'retrieve' or self.action == 'detail':
            return PointOfInterestDetailSerializer
        elif self.action == 'geojson':
            return PointOfInterestGeoJSONSerializer
        return PointOfInterestDetailSerializer

    @action(detail=False, methods=['get'])
    def geojson(self, request):
        """Return GeoJSON for all POIs."""
        queryset = self.get_queryset()
        serializer = PointOfInterestGeoJSONSerializer(queryset, many=True)
        # GeoFeatureModelSerializer with many=True returns a FeatureCollection directly
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Return detailed information for a POI."""
        try:
            instance = self.get_object()
            serializer = PointOfInterestDetailSerializer(instance)
            return Response(serializer.data)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in POI detail view: {e}", exc_info=True)
            from rest_framework import status as http_status
            return Response(
                {'error': str(e)},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        """Alias for retrieve using detail serializer."""
        return self.retrieve(request, pk=pk)


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

        # Find nearby launch points and POIs, grouped by section
        # Use dictionaries to track best distance for each point
        launch_points_by_section = {}  # section_id -> list of points
        pois_by_section = {}  # section_id -> list of points
        launch_point_best_distance = {}  # point_id -> (section_id, distance)
        poi_best_distance = {}  # poi_id -> (section_id, distance)

        # Get status filter
        status_filter = get_status_filter(request.user)

        for section in sections:
            # Use the LineString directly for distance queries
            # This finds points within distance of the line itself, not just sampled points
            # The distance is calculated to the nearest point on the line
            route_linestring = section.route
            
            # Find nearby launch points - distance is calculated to nearest point on the line
            nearby_lps = LaunchPoint.objects.filter(
                location__distance_lte=(route_linestring, D(m=search_radius_meters)),
                status__in=status_filter
            ).annotate(
                distance=Distance('location', route_linestring)
            ).order_by('distance').distinct()

            for lp in nearby_lps:
                distance_m = round(lp.distance.m, 0)
                # Check if this is the best distance for this launch point
                if lp.id not in launch_point_best_distance or distance_m < launch_point_best_distance[lp.id][1]:
                    # Remove from previous section if it was there
                    if lp.id in launch_point_best_distance:
                        prev_section_id = launch_point_best_distance[lp.id][0]
                        if prev_section_id in launch_points_by_section:
                            launch_points_by_section[prev_section_id] = [
                                p for p in launch_points_by_section[prev_section_id] if p['id'] != lp.id
                            ]
                    # Add to current section
                    launch_point_best_distance[lp.id] = (section.id, distance_m)
                    if section.id not in launch_points_by_section:
                        launch_points_by_section[section.id] = []
                    launch_points_by_section[section.id].append({
                        'id': lp.id,
                        'name': lp.name,
                        'distance_meters': distance_m,
                        'accessibility': lp.accessibility
                    })

            # Find nearby POIs - distance is calculated to nearest point on the line
            nearby_poi_list = PointOfInterest.objects.filter(
                location__distance_lte=(route_linestring, D(m=search_radius_meters)),
                status__in=status_filter
            ).annotate(
                distance=Distance('location', route_linestring)
            ).order_by('distance').distinct()

            for poi in nearby_poi_list:
                distance_m = round(poi.distance.m, 0)
                # Check if this is the best distance for this POI
                if poi.id not in poi_best_distance or distance_m < poi_best_distance[poi.id][1]:
                    # Remove from previous section if it was there
                    if poi.id in poi_best_distance:
                        prev_section_id = poi_best_distance[poi.id][0]
                        if prev_section_id in pois_by_section:
                            pois_by_section[prev_section_id] = [
                                p for p in pois_by_section[prev_section_id] if p['id'] != poi.id
                            ]
                    # Add to current section
                    poi_best_distance[poi.id] = (section.id, distance_m)
                    if section.id not in pois_by_section:
                        pois_by_section[section.id] = []
                    pois_by_section[section.id].append({
                        'id': poi.id,
                        'name': poi.name,
                        'poi_type': poi.poi_type.name,
                        'distance_meters': distance_m
                    })

        # Serialize sections
        section_serializer = RouteSectionGeoJSONSerializer(sections, many=True)
        waypoint_serializer = WaypointGeoJSONSerializer(waypoints, many=True)

        return Response({
            'sections': [
                {
                    'id': s.id,
                    'name': s.name or f"Section {s.id}",
                    'waterbody_name': s.waterbody.name if s.waterbody else None,
                    'distance_km': round(s.distance_meters / 1000.0, 2) if s.distance_meters else 0.0,
                    'from_waypoint': s.from_waypoint.name if s.from_waypoint else None,
                    'to_waypoint': s.to_waypoint.name if s.to_waypoint else None,
                    'launch_points': sorted(
                        launch_points_by_section.get(s.id, []),
                        key=lambda x: x['distance_meters']
                    ),
                    'pois': sorted(
                        pois_by_section.get(s.id, []),
                        key=lambda x: x['distance_meters']
                    ),
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

