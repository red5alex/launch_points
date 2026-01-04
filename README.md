# PaddleMap 🛶

A professional web application for planning watercraft tours (kayaks, SUPs, etc.) accessible by public transit. PaddleMap provides an interactive map interface to explore launch points, plan routes, and discover points of interest along waterways.

## Features

### Current Implementation

- **Interactive Map Interface**
  - Leaflet-based map with multiple layers (launch points, POIs, route sections, waypoints, transport stations, walk paths)
  - Click markers to view detailed information
  - Visual highlighting of selected launch points and POIs with radius circles
  - Status-based styling (approved content in full colors, pending content in lighter colors with dashed lines)

- **Tour Planning**
  - Select multiple route sections by clicking on the map
  - Automatic route calculation with nearby launch points and POIs
  - Configurable search radius (100-2000 meters) to find points of interest along routes
  - Visual route display with waypoint markers and waterbody information
  - Launch points and POIs grouped by route section

- **Content Management**
  - Database-backed storage using GeoDjango (Spatialite for development, MariaDB for production)
  - Django admin interface for content moderation
  - Status workflow: draft → pending → approved/rejected
  - Anonymous users see only approved content; logged-in users can see pending content

- **Data Import**
  - Import legacy data from CSV and GeoJSON files
  - Automatic image handling and storage
  - Support for transport types, launch points, POIs, route sections, stations, and walk paths

- **Internationalization**
  - Multi-language support (English and German)
  - Language switcher in navigation bar
  - URL-based language selection

- **API**
  - RESTful API with GeoJSON endpoints for all spatial data
  - Detailed endpoints for launch points and POIs (including images, comments, ratings)
  - Route calculation endpoint with distance-based point discovery

### Planned Features

- User authentication (login/register/logout)
- Content editing (create/update launch points, route sections)
- Image upload interface
- Comment and rating submission
- Route saving functionality
- HTMX integration for dynamic updates

## Using the Interface

### Map Navigation

- **Pan**: Click and drag the map
- **Zoom**: Use mouse wheel, zoom controls, or pinch gesture on touch devices
- **Reset view**: Use the zoom controls or click region links in the navigation bar

### Viewing Content

1. **Launch Points**: Displayed as blue markers on the map. Click a marker to view:
   - Name and location
   - Accessibility rating
   - Images (if available)
   - Comments and ratings
   - Nearby transport stations

2. **Points of Interest (POIs)**: Displayed as green markers. Click to view:
   - Name and type
   - Images (if available)
   - Comments and ratings

3. **Route Sections**: Displayed as blue lines connecting waypoints. Click a route section to:
   - Select it for tour planning
   - View waterbody name and section details

4. **Transport Stations**: Displayed with transport type icons. Show connections to launch points via walk paths.

### Planning a Tour

1. **Select Route Sections**:
   - Click on route sections (blue lines) on the map to add them to your tour
   - Selected sections are highlighted in red and appear thicker
   - Selected sections appear in the "Tour Planner" panel on the right

2. **Adjust Search Radius**:
   - Use the slider in the Tour Planner panel (100-2000 meters)
   - This determines how far from the route to search for launch points and POIs

3. **View Tour Details**:
   - The Tour Planner panel shows:
     - Selected route sections with waypoint markers
     - Waterbody names and section names
     - Launch points and POIs found along each section
     - Total tour distance
   - Waypoints are displayed as circles; shared waypoints between consecutive sections show as a single circle

4. **Deselect Sections**:
   - Click the red X button in the upper right corner of a route section in the Tour Planner panel
   - Or click the route section again on the map

### Viewing Details

- **Click any marker** (launch point, POI, or station) to load its details in the Info Box (right column)
- The Info Box shows:
  - Name and description
  - Images (click to view full size)
  - Ratings (accessibility, space, security)
  - Comments with user feedback
  - Related information (transport connections, etc.)

### Status Indicators

- **Approved content**: Full colors, solid lines
- **Pending content**: Lighter colors, dashed lines (visible only to logged-in users)
- **Selected markers**: Red circle overlay (100m radius) and larger red icon

### Language Switching

- Use the language switcher in the navigation bar to switch between English and German
- The interface language changes immediately, and URLs include language prefixes (`/en/`, `/de/`)

## Admin Interface

Access the Django admin at `http://127.0.0.1:8000/admin/` using your superuser credentials.

The admin interface allows you to:
- Approve/reject pending content
- Edit launch points, POIs, route sections, and other data
- Manage users and permissions
- View all content including pending items


## Installation

### Prerequisites

- Python 3.10 or higher
- GDAL and GEOS libraries (required for GeoDjango)
  - **Windows**: Use conda (recommended) or download from [OSGeo4W](https://trac.osgeo.org/osgeo4w/)
  - **Linux**: `sudo apt-get install gdal-bin libgdal-dev geos libgeos-dev`
  - **macOS**: `brew install gdal geos`

### Option 1: Conda Environment (Recommended for Windows)

1. **Create conda environment with GDAL/GEOS**:
   ```powershell
   conda create -n paddlemap python=3.11 -c conda-forge gdal geos
   conda activate paddlemap
   ```

2. **Install Python dependencies**:
   ```powershell
   pip install --upgrade pip
   pip install -r requirements_web.txt
   ```

### Option 2: Python Virtual Environment

1. **Create virtual environment**:
   ```powershell
   # Windows PowerShell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   
   # Linux/macOS
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install GDAL/GEOS** (if not using conda):
   - Windows: Install from OSGeo4W or use conda
   - Linux: `sudo apt-get install gdal-bin libgdal-dev geos libgeos-dev`
   - macOS: `brew install gdal geos`

3. **Set environment variables** (if GDAL/GEOS not in system PATH):
   ```powershell
   # Windows - adjust paths as needed
   $env:GDAL_LIBRARY_PATH = "C:\path\to\gdal.dll"
   $env:GEOS_LIBRARY_PATH = "C:\path\to\geos_c.dll"
   ```

4. **Install Python dependencies**:
   ```powershell
   pip install --upgrade pip
   pip install -r requirements_web.txt
   ```

## Django Setup

1. **Set Django settings module** (if not using default):
   ```powershell
   # Windows PowerShell
   $env:DJANGO_SETTINGS_MODULE = "launch_points_web.settings.development"
   
   # Linux/macOS
   export DJANGO_SETTINGS_MODULE=launch_points_web.settings.development
   ```

2. **Create database migrations**:
   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Create superuser** (for admin access):
   ```powershell
   python manage.py createsuperuser
   ```
   Follow the prompts to create an admin account.

4. **Import legacy data** (optional, if you have data files in `berlin/` directory):
   ```powershell
   python manage.py import_legacy_data --data-dir berlin
   ```
   This command imports:
   - Transport types from `berlin/transport_types.json`
   - Launch points from `berlin/launch_with_transport.csv` and `berlin/launch_without_transport.csv`
   - POIs from `berlin/resting_points.csv`
   - Route sections from `berlin/routes.geojson`
   - Stations and walk paths from `berlin/station_paths.geojson`
   - Images copied to `media/images/`

   Use `--dry-run` to preview what would be imported without making changes.

5. **Collect static files**:
   ```powershell
   python manage.py collectstatic --noinput
   ```

6. **Start development server**:
   ```powershell
   python manage.py runserver
   ```

The application will be available at `http://127.0.0.1:8000/`


## Project Structure

```
launch_points_web/
├── manage.py
├── requirements_web.txt
├── launch_points_web/          # Main Django project
│   ├── settings/
│   │   ├── base.py              # Base settings (GeoDjango, i18n, media)
│   │   ├── development.py       # Spatialite config
│   │   └── production.py        # MariaDB config
│   └── urls.py                  # Root URL config with i18n
├── core/                        # Main application
│   ├── models.py                # All GeoDjango models
│   ├── admin.py                 # Django admin
│   ├── serializers.py           # DRF serializers (GeoJSON + detail)
│   ├── api_views.py             # API viewsets and route calculation
│   ├── views.py                 # Main map view
│   └── management/commands/
│       └── import_legacy_data.py  # Data migration from CSV/GeoJSON
├── templates/
│   ├── base.html                # Base template (navbar, i18n)
│   └── map.html                 # Main map view template
├── static/
│   ├── css/
│   │   └── main.css             # Map-centric layout, sidebar styles
│   └── js/
│       ├── map.js               # Leaflet map init, layer loading
│       ├── route_selection.js   # Route selection logic, tour planner
│       └── htmx_integration.js  # HTMX handlers (placeholder)
└── media/                       # User-uploaded images
    └── images/                  # Unified image storage
```

## Troubleshooting

### GDAL/GEOS Not Found

**Windows (Conda)**:
- Ensure you're using a conda environment with GDAL/GEOS installed
- The settings file auto-detects conda paths

**Windows (venv)**:
- Set `GDAL_LIBRARY_PATH` and `GEOS_LIBRARY_PATH` environment variables
- Or install GDAL/GEOS via OSGeo4W and add to system PATH

**Linux/macOS**:
- Install via package manager: `apt-get install` (Linux) or `brew install` (macOS)

### Database Errors

- Ensure migrations are up to date: `python manage.py migrate`
- For Spatialite issues, ensure the spatialite extension is available (usually included with GeoDjango)

### Static Files Not Loading

- Run `python manage.py collectstatic`
- Ensure `DEBUG=True` in development settings (serves static files automatically)

### Import Errors

- Check that data files exist in the specified directory
- Use `--dry-run` to preview imports
- Ensure CSV files have correct headers (no leading/trailing spaces)
- Verify image paths in CSV files are correct relative to the data directory

## Development

### Running Tests

```powershell
python manage.py test
```

### Creating Migrations

After modifying models:
```powershell
python manage.py makemigrations
python manage.py migrate
```

### Translation Updates

After adding new translatable strings:
```powershell
python manage.py makemessages -l de
python manage.py makemessages -l en
python manage.py compilemessages
```

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please ensure:
- Code follows Django and Python best practices
- Spatial queries use GeoDjango functions
- Status filtering respects user authentication
- Translations are updated for new user-facing strings
