"""
Management command to import legacy data from CSV and GeoJSON files.

Usage:
    python manage.py import_legacy_data
    python manage.py import_legacy_data --data-dir berlin
"""
import json
import os
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point, LineString, Polygon
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from geopy.distance import distance as geopy_distance

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

from core.models import (
    Region, TransportType, POIType, RouteType, Waterbody,
    PublicTransportStation, LaunchPoint, PointOfInterest, Waypoint,
    RouteSection, WalkPath, Image
)


class Command(BaseCommand):
    help = 'Import legacy data from CSV and GeoJSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            type=str,
            default='berlin',
            help='Directory containing legacy data files (default: berlin)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )

    def handle(self, *args, **options):
        data_dir = Path(options['data_dir'])
        dry_run = options['dry_run']

        if not data_dir.exists():
            self.stdout.write(self.style.ERROR(f'Data directory not found: {data_dir}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Importing data from: {data_dir}'))
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be imported'))

        # Step 1: Create initial data (regions, types, etc.)
        self.create_initial_data(dry_run)

        # Step 2: Import transport types
        self.import_transport_types(data_dir, dry_run)

        # Step 3: Import launch points
        self.import_launch_points(data_dir, dry_run)

        # Step 4: Import POIs
        self.import_pois(data_dir, dry_run)

        # Step 5: Import route sections
        self.import_route_sections(data_dir, dry_run)

        # Step 6: Import stations and walk paths
        self.import_stations_and_walk_paths(data_dir, dry_run)

        self.stdout.write(self.style.SUCCESS('Import completed!'))

    def create_initial_data(self, dry_run):
        """Create initial reference data."""
        self.stdout.write('Creating initial reference data...')

        # Create Berlin region
        if not dry_run:
            region, created = Region.objects.get_or_create(
                name='Berlin (Germany)',
                defaults={
                    'bounding_box': Polygon.from_bbox((13.0, 52.3, 13.8, 52.7))  # Approximate Berlin bounds
                }
            )
            if created:
                self.stdout.write(f'  Created region: {region.name}')

        # Create route types
        route_types_data = [
            {'name': 'primary', 'display_name': 'Primary Route'},
            {'name': 'secondary', 'display_name': 'Secondary Route'},
        ]
        for rt_data in route_types_data:
            if not dry_run:
                rt, created = RouteType.objects.get_or_create(
                    name=rt_data['name'],
                    defaults={'display_name': rt_data['display_name']}
                )
                if created:
                    self.stdout.write(f'  Created route type: {rt.display_name}')

        # Create POI type for resting points
        if not dry_run:
            poi_type, created = POIType.objects.get_or_create(
                name='resting',
                defaults={'icon_class': 'fa-solid fa-umbrella-beach'}
            )
            if created:
                self.stdout.write(f'  Created POI type: {poi_type.name}')

    def import_transport_types(self, data_dir, dry_run):
        """Import transport types from JSON file."""
        self.stdout.write('Importing transport types...')
        transport_file = data_dir / 'transport_types.json'

        if not transport_file.exists():
            self.stdout.write(self.style.WARNING(f'  Transport types file not found: {transport_file}'))
            return

        with open(transport_file, 'r', encoding='utf-8') as f:
            transport_data = json.load(f)

        for key, value in transport_data.items():
            if not dry_run:
                tt, created = TransportType.objects.get_or_create(
                    key=key,
                    defaults={
                        'name': value.get('name', key),
                        'icon_class': value.get('icon', value.get('icon_class', ''))
                    }
                )
                if created:
                    self.stdout.write(f'  Created transport type: {tt.name}')

    def import_launch_points(self, data_dir, dry_run):
        """Import launch points from CSV files."""
        self.stdout.write('Importing launch points...')

        if not HAS_PANDAS:
            self.stdout.write(self.style.ERROR('  pandas is required for CSV import. Install with: pip install pandas'))
            return

        csv_files = [
            (data_dir / 'launch_with_transport.csv', True),
            (data_dir / 'launch_without_transport.csv', False),
        ]

        for csv_file, has_transport in csv_files:
            if not csv_file.exists():
                self.stdout.write(self.style.WARNING(f'  File not found: {csv_file}'))
                continue

            df = pd.read_csv(csv_file)

            # Normalize column names
            df.columns = [c.strip() for c in df.columns]

            for _, row in df.iterrows():
                name = str(row.get('name', '')).strip()
                if not name:
                    continue

                try:
                    lat = float(str(row.get('lat', '')).strip().replace(',', '.'))
                    lon = float(str(row.get('lon', '')).strip().replace(',', '.'))
                except (ValueError, TypeError):
                    self.stdout.write(self.style.WARNING(f'  Skipping {name}: invalid coordinates'))
                    continue

                location = Point(lon, lat, srid=4326)
                accessibility = str(row.get('accessibility', '')).strip().lower()
                if accessibility not in ['good', 'moderate', 'poor']:
                    accessibility = ''

                picture_path = str(row.get('picture', '')).strip()

                if not dry_run:
                    lp, created = LaunchPoint.objects.get_or_create(
                        name=name,
                        defaults={
                            'location': location,
                            'accessibility': accessibility,
                            'status': 'approved'  # Legacy data is pre-approved
                        }
                    )

                    if created:
                        self.stdout.write(f'  Created launch point: {lp.name}')

                        # Handle image if present
                        if picture_path:
                            self.copy_image(picture_path, data_dir, lp, dry_run)
                    else:
                        self.stdout.write(f'  Launch point already exists: {lp.name}')

    def import_pois(self, data_dir, dry_run):
        """Import POIs from CSV file."""
        self.stdout.write('Importing POIs...')
        csv_file = data_dir / 'resting_points.csv'

        if not csv_file.exists():
            self.stdout.write(self.style.WARNING(f'  File not found: {csv_file}'))
            return

        if not HAS_PANDAS:
            self.stdout.write(self.style.ERROR('  pandas is required for CSV import. Install with: pip install pandas'))
            return

        df = pd.read_csv(csv_file)

        # Normalize column names
        df.columns = [c.strip() for c in df.columns]

        # Get or create resting POI type
        if not dry_run:
            poi_type, _ = POIType.objects.get_or_create(name='resting')

        for _, row in df.iterrows():
            name = str(row.get('name', '')).strip()
            if not name:
                continue

            try:
                lat = float(str(row.get('lat', '')).strip().replace(',', '.'))
                lon = float(str(row.get('lon', '')).strip().replace(',', '.'))
            except (ValueError, TypeError):
                self.stdout.write(self.style.WARNING(f'  Skipping {name}: invalid coordinates'))
                continue

            location = Point(lon, lat, srid=4326)
            accessibility = str(row.get('accessibility', '')).strip().lower()
            if accessibility not in ['good', 'moderate', 'poor']:
                accessibility = ''

            if not dry_run:
                poi, created = PointOfInterest.objects.get_or_create(
                    name=name,
                    defaults={
                        'location': location,
                        'poi_type': poi_type,
                        'accessibility': accessibility,
                        'status': 'approved'
                    }
                )

                if created:
                    self.stdout.write(f'  Created POI: {poi.name}')

    def import_route_sections(self, data_dir, dry_run):
        """Import route sections from GeoJSON file."""
        self.stdout.write('Importing route sections...')
        geojson_file = data_dir / 'routes.geojson'

        if not geojson_file.exists():
            self.stdout.write(self.style.WARNING(f'  File not found: {geojson_file}'))
            return

        with open(geojson_file, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)

        # Get route types (always get them, even in dry-run for reference)
        primary_type = None
        secondary_type = None
        if not dry_run:
            primary_type, _ = RouteType.objects.get_or_create(name='primary')
            secondary_type, _ = RouteType.objects.get_or_create(name='secondary')
        else:
            # In dry-run, just create dummy references
            self.stdout.write('  Would create route types: primary, secondary')

        # Track waypoints by location (to avoid duplicates)
        waypoint_cache = {}
        # Cache for waterbodies (created on-the-fly)
        waterbody_cache = {}

        for feature in geojson_data.get('features', []):
            props = feature.get('properties', {})
            geom = feature.get('geometry', {})

            if geom.get('type') != 'LineString':
                continue

            coords = geom.get('coordinates', [])
            if len(coords) < 2:
                continue

            # Create LineString geometry
            line_coords = [(coord[0], coord[1]) for coord in coords]
            route_geom = LineString(line_coords, srid=4326)

            # Calculate distance in meters
            total_distance_m = 0.0
            for i in range(len(line_coords) - 1):
                p1 = line_coords[i]
                p2 = line_coords[i + 1]
                total_distance_m += geopy_distance((p1[1], p1[0]), (p2[1], p2[0])).meters

            # Get or create waterbody
            waterbody_name = props.get('waterbody', '').strip()
            if not waterbody_name:
                # Use default waterbody name if missing
                waterbody_name = 'Unknown'
                self.stdout.write(self.style.WARNING(f'  Route missing waterbody, using "Unknown"'))

            if not dry_run:
                # Get or create waterbody (cache to avoid repeated DB queries)
                if waterbody_name not in waterbody_cache:
                    wb, created = Waterbody.objects.get_or_create(name=waterbody_name)
                    waterbody_cache[waterbody_name] = wb
                    if created:
                        self.stdout.write(f'  Created waterbody: {wb.name}')
                waterbody = waterbody_cache[waterbody_name]
            else:
                # Dry run: just track the name
                if waterbody_name not in waterbody_cache:
                    waterbody_cache[waterbody_name] = waterbody_name
                    self.stdout.write(f'  Would create waterbody: {waterbody_name}')
                waterbody = None  # Not used in dry run

            # Determine route type (from is_sidetrack property, default to primary)
            is_sidetrack = props.get('sidetrack', False)
            if dry_run:
                route_type_name = 'secondary' if is_sidetrack else 'primary'
                self.stdout.write(f'  Would assign route type: {route_type_name}')
            else:
                route_type = secondary_type if is_sidetrack else primary_type

            # Get or create waypoints for start and end
            start_coord = coords[0]
            end_coord = coords[-1]

            from_waypoint = None
            to_waypoint = None

            if dry_run:
                # Dry run: just show what would be created
                start_name = props.get('start', '').strip() or 'unnamed'
                end_name = props.get('end', '').strip() or 'unnamed'
                route_name = props.get('name', '').strip() or 'unnamed'
                self.stdout.write(f'  Would create route section: {route_name} ({start_name} → {end_name}, {total_distance_m/1000:.2f} km)')
            else:
                # Create or get waypoint for start
                start_key = (round(start_coord[0], 6), round(start_coord[1], 6))
                if start_key not in waypoint_cache:
                    start_point = Point(start_coord[0], start_coord[1], srid=4326)
                    wp_name = props.get('start', '').strip() or None
                    waypoint_cache[start_key] = Waypoint.objects.create(
                        name=wp_name,
                        location=start_point
                    )
                from_waypoint = waypoint_cache[start_key]

                # Create or get waypoint for end
                end_key = (round(end_coord[0], 6), round(end_coord[1], 6))
                if end_key not in waypoint_cache:
                    end_point = Point(end_coord[0], end_coord[1], srid=4326)
                    wp_name = props.get('end', '').strip() or None
                    waypoint_cache[end_key] = Waypoint.objects.create(
                        name=wp_name,
                        location=end_point
                    )
                to_waypoint = waypoint_cache[end_key]

                # Create route section
                try:
                    route_name = props.get('name', '').strip() or ''  # Empty string, not None
                    route_section = RouteSection.objects.create(
                        name=route_name,
                        route=route_geom,
                        from_waypoint=from_waypoint,
                        to_waypoint=to_waypoint,
                        waterbody=waterbody,
                        distance_meters=total_distance_m,
                        status='approved'
                    )

                    # Add route type
                    route_section.route_types.add(route_type)

                    self.stdout.write(f'  Created route section: {route_section.name or route_section.id} ({total_distance_m/1000:.2f} km)')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  Error creating route section: {e}'))
                    continue

    def import_stations_and_walk_paths(self, data_dir, dry_run):
        """Import stations and walk paths from GeoJSON file."""
        self.stdout.write('Importing stations and walk paths...')
        geojson_file = data_dir / 'station_paths.geojson'

        if not geojson_file.exists():
            self.stdout.write(self.style.WARNING(f'  File not found: {geojson_file}'))
            return

        with open(geojson_file, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)

        if not dry_run:
            # Get transport types
            transport_types = {}
            for tt in TransportType.objects.all():
                transport_types[tt.key] = tt

        for feature in geojson_data.get('features', []):
            props = feature.get('properties', {})
            geom = feature.get('geometry', {})

            if geom.get('type') != 'LineString':
                continue

            coords = geom.get('coordinates', [])
            if len(coords) < 2:
                continue

            # First vertex is the station location
            station_coord = coords[0]
            station_location = Point(station_coord[0], station_coord[1], srid=4326)

            # Station name and type
            station_name = props.get('station_name') or props.get('name', '').strip()
            station_type_key = (props.get('station_type') or props.get('type', 'bus')).lower().strip()

            if not station_name:
                self.stdout.write(self.style.WARNING('  Skipping station: missing name'))
                continue

            if not dry_run:
                # Get transport type
                transport_type = transport_types.get(station_type_key)
                if not transport_type:
                    self.stdout.write(self.style.WARNING(f'  Unknown transport type: {station_type_key}'))
                    continue

                # Create or get station
                station, created = PublicTransportStation.objects.get_or_create(
                    name=station_name,
                    location=station_location,
                    defaults={'status': 'approved'}
                )

                if created:
                    station.station_types.add(transport_type)
                    self.stdout.write(f'  Created station: {station.name}')

                # Create walk path (from station to last point)
                # Find nearest launch point to the end of the path
                path_end = Point(coords[-1][0], coords[-1][1], srid=4326)

                # Find nearest launch point using spatial query with distance annotation
                nearest_lp = LaunchPoint.objects.filter(
                    location__distance_lte=(path_end, D(km=1))  # Within 1km
                ).annotate(
                    distance=Distance('location', path_end)
                ).order_by('distance').first()

                if nearest_lp:
                    # Create LineString for walk path
                    path_coords = [(c[0], c[1]) for c in coords]
                    path_geom = LineString(path_coords, srid=4326)

                    # Calculate distance
                    total_distance_m = 0.0
                    for i in range(len(path_coords) - 1):
                        p1 = path_coords[i]
                        p2 = path_coords[i + 1]
                        total_distance_m += geopy_distance((p1[1], p1[0]), (p2[1], p2[0])).meters

                    walk_path, created = WalkPath.objects.get_or_create(
                        station=station,
                        launch_point=nearest_lp,
                        defaults={
                            'path': path_geom,
                            'distance_meters': total_distance_m,
                        }
                    )

                    if created:
                        self.stdout.write(f'  Created walk path: {station.name} → {nearest_lp.name} ({total_distance_m:.0f}m)')

    def copy_image(self, picture_path, data_dir, content_object, dry_run):
        """Copy image file to media directory and create Image record."""
        source_path = data_dir / picture_path

        if not source_path.exists():
            self.stdout.write(self.style.WARNING(f'  Image not found: {source_path}'))
            return

        if dry_run:
            self.stdout.write(f'  Would copy image: {source_path}')
            return

        # Create media/images directory if it doesn't exist
        media_dir = Path('media/images')
        media_dir.mkdir(parents=True, exist_ok=True)

        # Copy file
        dest_path = media_dir / source_path.name
        shutil.copy2(source_path, dest_path)

        # Create Image record
        content_type = ContentType.objects.get_for_model(content_object)
        Image.objects.create(
            content_type=content_type,
            object_id=content_object.id,
            image=f'images/{source_path.name}',
            caption=content_object.name
        )

        self.stdout.write(f'  Copied image: {source_path.name}')

