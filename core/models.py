"""
Core models for Launch Points Web application.
"""
from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.utils.translation import gettext_lazy as _


class Region(models.Model):
    """Map regions for navigation shortcuts."""
    name = models.CharField(max_length=200, verbose_name=_('Name'))
    bounding_box = models.PolygonField(verbose_name=_('Bounding Box'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Region')
        verbose_name_plural = _('Regions')
        ordering = ['name']

    def __str__(self):
        return self.name


class TransportType(models.Model):
    """Transport type configuration."""
    key = models.CharField(max_length=50, unique=True, verbose_name=_('Key'))
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    icon_class = models.CharField(max_length=100, verbose_name=_('Icon Class'))

    class Meta:
        verbose_name = _('Transport Type')
        verbose_name_plural = _('Transport Types')
        ordering = ['name']

    def __str__(self):
        return self.name


class POIType(models.Model):
    """Point of interest type configuration."""
    name = models.CharField(max_length=100, unique=True, verbose_name=_('Name'))
    icon_class = models.CharField(max_length=100, verbose_name=_('Icon Class'))

    class Meta:
        verbose_name = _('POI Type')
        verbose_name_plural = _('POI Types')
        ordering = ['name']

    def __str__(self):
        return self.name


class RouteType(models.Model):
    """Route type classification."""
    name = models.CharField(max_length=50, unique=True, verbose_name=_('Name'))
    display_name = models.CharField(max_length=100, verbose_name=_('Display Name'))

    class Meta:
        verbose_name = _('Route Type')
        verbose_name_plural = _('Route Types')
        ordering = ['name']

    def __str__(self):
        return self.display_name


class Waterbody(models.Model):
    """Waterbody picklist."""
    name = models.CharField(max_length=200, unique=True, verbose_name=_('Name'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Waterbody')
        verbose_name_plural = _('Waterbodies')
        ordering = ['name']

    def __str__(self):
        return self.name


class PublicTransportStation(models.Model):
    """Public transport stations."""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]

    name = models.CharField(max_length=200, verbose_name=_('Name'))
    location = models.PointField(verbose_name=_('Location'))
    station_types = models.ManyToManyField(TransportType, verbose_name=_('Station Types'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_stations', verbose_name=_('Created By')
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='updated_stations', verbose_name=_('Updated By')
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending',
        verbose_name=_('Status')
    )

    class Meta:
        verbose_name = _('Public Transport Station')
        verbose_name_plural = _('Public Transport Stations')
        ordering = ['name']

    def __str__(self):
        return self.name


class LaunchPoint(models.Model):
    """Launch points for watercraft."""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]
    ACCESSIBILITY_CHOICES = [
        ('good', _('Good')),
        ('moderate', _('Moderate')),
        ('poor', _('Poor')),
    ]

    name = models.CharField(max_length=200, verbose_name=_('Name'))
    location = models.PointField(verbose_name=_('Location'))
    accessibility = models.CharField(
        max_length=20, choices=ACCESSIBILITY_CHOICES, blank=True,
        verbose_name=_('Accessibility')
    )
    description = models.TextField(blank=True, verbose_name=_('Description'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_launch_points', verbose_name=_('Created By')
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='updated_launch_points', verbose_name=_('Updated By')
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending',
        verbose_name=_('Status')
    )

    # Generic relation to Image model
    images = GenericRelation('Image', related_query_name='launch_point')
    # Generic relation to Comment model
    comments = GenericRelation('Comment', related_query_name='launch_point')

    class Meta:
        verbose_name = _('Launch Point')
        verbose_name_plural = _('Launch Points')
        ordering = ['name']

    def __str__(self):
        return self.name


class PointOfInterest(models.Model):
    """General points of interest (replaces RestingPoint)."""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]
    ACCESSIBILITY_CHOICES = [
        ('good', _('Good')),
        ('moderate', _('Moderate')),
        ('poor', _('Poor')),
    ]

    name = models.CharField(max_length=200, verbose_name=_('Name'))
    location = models.PointField(verbose_name=_('Location'))
    poi_type = models.ForeignKey(
        POIType, on_delete=models.PROTECT, verbose_name=_('POI Type')
    )
    accessibility = models.CharField(
        max_length=20, choices=ACCESSIBILITY_CHOICES, blank=True,
        verbose_name=_('Accessibility')
    )
    description = models.TextField(blank=True, verbose_name=_('Description'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_pois', verbose_name=_('Created By')
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='updated_pois', verbose_name=_('Updated By')
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending',
        verbose_name=_('Status')
    )

    # Generic relation to Image model
    images = GenericRelation('Image', related_query_name='poi')
    # Generic relation to Comment model
    comments = GenericRelation('Comment', related_query_name='poi')

    class Meta:
        verbose_name = _('Point of Interest')
        verbose_name_plural = _('Points of Interest')
        ordering = ['name']

    def __str__(self):
        return self.name


class Waypoint(models.Model):
    """Junction points connecting RouteSections."""
    name = models.CharField(max_length=200, blank=True, verbose_name=_('Name'))
    location = models.PointField(verbose_name=_('Location'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_waypoints', verbose_name=_('Created By')
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='updated_waypoints', verbose_name=_('Updated By')
    )

    class Meta:
        verbose_name = _('Waypoint')
        verbose_name_plural = _('Waypoints')
        ordering = ['name']

    def __str__(self):
        return self.name or f"Waypoint {self.id}"


class RouteSection(models.Model):
    """Route sections over water (replaces WaterRoute)."""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]

    name = models.CharField(max_length=200, blank=True, verbose_name=_('Name'))
    route = models.LineStringField(verbose_name=_('Route'))
    from_waypoint = models.ForeignKey(
        Waypoint, on_delete=models.PROTECT, null=True, blank=True,
        related_name='outgoing_sections', verbose_name=_('From Waypoint')
    )
    to_waypoint = models.ForeignKey(
        Waypoint, on_delete=models.PROTECT, null=True, blank=True,
        related_name='incoming_sections', verbose_name=_('To Waypoint')
    )
    waterbody = models.ForeignKey(
        Waterbody, on_delete=models.PROTECT, verbose_name=_('Waterbody')
    )
    route_types = models.ManyToManyField(
        RouteType, verbose_name=_('Route Types')
    )
    distance_meters = models.FloatField(verbose_name=_('Distance (meters)'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_route_sections', verbose_name=_('Created By')
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='updated_route_sections', verbose_name=_('Updated By')
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending',
        verbose_name=_('Status')
    )

    class Meta:
        verbose_name = _('Route Section')
        verbose_name_plural = _('Route Sections')
        constraints = [
            models.CheckConstraint(
                check=~models.Q(from_waypoint__isnull=True) | ~models.Q(to_waypoint__isnull=True),
                name='at_least_one_waypoint'
            )
        ]

    def __str__(self):
        return self.name or f"Route Section {self.id}"

    @property
    def distance_km(self):
        """Convert distance from meters to kilometers."""
        return self.distance_meters / 1000.0


class WalkPath(models.Model):
    """Walking paths from stations to launch points."""
    station = models.ForeignKey(
        PublicTransportStation, on_delete=models.CASCADE,
        related_name='walk_paths', verbose_name=_('Station')
    )
    launch_point = models.ForeignKey(
        LaunchPoint, on_delete=models.CASCADE,
        related_name='walk_paths', verbose_name=_('Launch Point')
    )
    path = models.LineStringField(verbose_name=_('Path'))
    distance_meters = models.FloatField(verbose_name=_('Distance (meters)'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_walk_paths', verbose_name=_('Created By')
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='updated_walk_paths', verbose_name=_('Updated By')
    )

    class Meta:
        verbose_name = _('Walk Path')
        verbose_name_plural = _('Walk Paths')

    def __str__(self):
        return f"{self.station.name} → {self.launch_point.name}"


class SavedRoute(models.Model):
    """User-saved route selections."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='saved_routes',
        verbose_name=_('User')
    )
    name = models.CharField(max_length=200, verbose_name=_('Name'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    sections = models.ManyToManyField(
        RouteSection, verbose_name=_('Sections')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Saved Route')
        verbose_name_plural = _('Saved Routes')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.name}"


class Image(models.Model):
    """Generalized image model (replaces LaunchPointImage)."""
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    image = models.ImageField(
        upload_to='images/', verbose_name=_('Image')
    )
    caption = models.CharField(
        max_length=200, blank=True, verbose_name=_('Caption')
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Uploaded By')
    )

    class Meta:
        verbose_name = _('Image')
        verbose_name_plural = _('Images')
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Image {self.id} - {self.content_object}"


class Comment(models.Model):
    """User comments on launch points or POIs."""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments',
        verbose_name=_('User')
    )
    text = models.TextField(verbose_name=_('Text'))
    needs_fixing = models.BooleanField(
        default=False, verbose_name=_('Needs Fixing')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending',
        verbose_name=_('Status')
    )

    # Generic relation to Image model (comments can have images)
    images = GenericRelation('Image', related_query_name='comment')

    class Meta:
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.content_object}"


class Rating(models.Model):
    """Ratings within comments (replaces Vote)."""
    CATEGORY_CHOICES = [
        ('accessibility', _('Accessibility')),
        ('space', _('Space for Setting Up')),
        ('security', _('Security')),
    ]

    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name='ratings',
        verbose_name=_('Comment')
    )
    category = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, verbose_name=_('Category')
    )
    value = models.IntegerField(verbose_name=_('Value'))  # 1-5 scale
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Rating')
        verbose_name_plural = _('Ratings')
        unique_together = [['comment', 'category']]
        ordering = ['category']

    def __str__(self):
        return f"{self.comment} - {self.get_category_display()}: {self.value}"

