"""
DRF serializers for core models.
"""
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.contenttypes.models import ContentType
from .models import (
    Region, TransportType, POIType, RouteType, Waterbody,
    PublicTransportStation, LaunchPoint, PointOfInterest, Waypoint,
    RouteSection, WalkPath, SavedRoute, Image, Comment, Rating
)


class RegionSerializer(serializers.ModelSerializer):
    """Serializer for Region model."""
    class Meta:
        model = Region
        fields = ['id', 'name', 'bounding_box']


class LaunchPointGeoJSONSerializer(GeoFeatureModelSerializer):
    """GeoJSON serializer for LaunchPoint."""
    accessibility_display = serializers.CharField(source='get_accessibility_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    image_count = serializers.SerializerMethodField()

    class Meta:
        model = LaunchPoint
        geo_field = 'location'
        fields = ['id', 'name', 'accessibility', 'accessibility_display', 'status', 'status_display', 'image_count']

    def get_image_count(self, obj):
        return obj.images.count()


class PointOfInterestGeoJSONSerializer(GeoFeatureModelSerializer):
    """GeoJSON serializer for PointOfInterest."""
    poi_type_name = serializers.CharField(source='poi_type.name', read_only=True)
    accessibility_display = serializers.CharField(source='get_accessibility_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    image_count = serializers.SerializerMethodField()

    class Meta:
        model = PointOfInterest
        geo_field = 'location'
        fields = ['id', 'name', 'poi_type_name', 'accessibility', 'accessibility_display', 'status', 'status_display', 'image_count']

    def get_image_count(self, obj):
        return obj.images.count()


class RouteSectionGeoJSONSerializer(GeoFeatureModelSerializer):
    """GeoJSON serializer for RouteSection."""
    waterbody_name = serializers.CharField(source='waterbody.name', read_only=True)
    route_types = serializers.SerializerMethodField()
    distance_km = serializers.FloatField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = RouteSection
        geo_field = 'route'
        fields = ['id', 'name', 'waterbody_name', 'route_types', 'distance_meters', 'distance_km', 'status', 'status_display']
        fields = ['id', 'name', 'waterbody_name', 'route_types', 'distance_meters', 'distance_km', 'status', 'status_display']

    def get_route_types(self, obj):
        return [rt.name for rt in obj.route_types.all()]


class WaypointGeoJSONSerializer(GeoFeatureModelSerializer):
    """GeoJSON serializer for Waypoint."""
    class Meta:
        model = Waypoint
        geo_field = 'location'
        fields = ['id', 'name']


class PublicTransportStationGeoJSONSerializer(GeoFeatureModelSerializer):
    """GeoJSON serializer for PublicTransportStation."""
    station_types = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PublicTransportStation
        geo_field = 'location'
        fields = ['id', 'name', 'station_types', 'status', 'status_display']

    def get_station_types(self, obj):
        return [{'key': st.key, 'name': st.name, 'icon': st.icon_class} for st in obj.station_types.all()]


class WalkPathGeoJSONSerializer(GeoFeatureModelSerializer):
    """GeoJSON serializer for WalkPath."""
    station_name = serializers.CharField(source='station.name', read_only=True)
    launch_point_name = serializers.CharField(source='launch_point.name', read_only=True)

    class Meta:
        model = WalkPath
        geo_field = 'path'
        fields = ['id', 'station_name', 'launch_point_name', 'distance_meters']


class ImageSerializer(serializers.ModelSerializer):
    """Serializer for Image model."""
    class Meta:
        model = Image
        fields = ['id', 'image', 'caption', 'uploaded_at']


class RatingSerializer(serializers.ModelSerializer):
    """Serializer for Rating model."""
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Rating
        fields = ['id', 'category', 'category_display', 'value', 'created_at']


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model."""
    user_username = serializers.CharField(source='user.username', read_only=True)
    images = ImageSerializer(many=True, read_only=True)
    ratings = RatingSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user_username', 'text', 'needs_fixing', 'images', 'ratings', 'status', 'status_display', 'created_at', 'updated_at']


class LaunchPointDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for LaunchPoint."""
    images = ImageSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    accessibility_display = serializers.CharField(source='get_accessibility_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    # Aggregate ratings from approved comments
    average_ratings = serializers.SerializerMethodField()

    class Meta:
        model = LaunchPoint
        fields = [
            'id', 'name', 'location', 'accessibility', 'accessibility_display',
            'description', 'status', 'status_display', 'images', 'comments',
            'average_ratings', 'created_at', 'updated_at'
        ]

    def get_average_ratings(self, obj):
        """Calculate average ratings from approved comments."""
        from django.db.models import Avg
        approved_comments = obj.comments.filter(status='approved')
        ratings = Rating.objects.filter(comment__in=approved_comments)
        
        result = {}
        for category in ['accessibility', 'space', 'security']:
            category_ratings = ratings.filter(category=category)
            if category_ratings.exists():
                result[category] = {
                    'average': round(category_ratings.aggregate(Avg('value'))['value__avg'], 2),
                    'count': category_ratings.count()
                }
        return result

    def to_representation(self, instance):
        """Convert location to lat/lon format."""
        data = super().to_representation(instance)
        if instance.location:
            data['location'] = {
                'lat': instance.location.y,
                'lon': instance.location.x
            }
        return data


class PointOfInterestDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for PointOfInterest."""
    poi_type_name = serializers.CharField(source='poi_type.name', read_only=True)
    poi_type_icon = serializers.CharField(source='poi_type.icon_class', read_only=True)
    images = ImageSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    accessibility_display = serializers.CharField(source='get_accessibility_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PointOfInterest
        fields = [
            'id', 'name', 'location', 'poi_type_name', 'poi_type_icon',
            'accessibility', 'accessibility_display', 'description',
            'status', 'status_display', 'images', 'comments',
            'created_at', 'updated_at'
        ]

    def to_representation(self, instance):
        """Convert location to lat/lon format."""
        data = super().to_representation(instance)
        if instance.location:
            data['location'] = {
                'lat': instance.location.y,
                'lon': instance.location.x
            }
        return data
