# Launch Points Web Framework

Professional web application for managing and displaying launch points, routes, and points of interest for watercraft accessible by public transit.

## Features

- Interactive Leaflet map with GeoDjango backend
- Database-backed data storage (Spatialite for development, MariaDB for production)
- Multi-lingual support (German and English)
- User authentication and moderation workflow
- Route selection and planning
- Comments and ratings system
- Image uploads for launch points, POIs, and comments

## Technology Stack

- **Backend**: Django 4.2+ with GeoDjango
- **Database**: Spatialite (development) / MariaDB (production)
- **Frontend**: HTMX + Leaflet
- **API**: Django REST Framework with GIS extensions

## Setup Instructions

### Prerequisites

1. Python 3.10 or higher
2. GDAL and GEOS libraries (required for GeoDjango)
   - Windows: Download from [OSGeo4W](https://trac.osgeo.org/osgeo4w/) or use conda
   - Linux: `sudo apt-get install gdal-bin libgdal-dev geos libgeos-dev`
   - macOS: `brew install gdal geos`

### Installation

1. **Create and activate virtual environment**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. **Install dependencies**:
   ```powershell
   pip install --upgrade pip
   pip install -r requirements_web.txt
   ```

3. **Set up environment variables** (optional, for production):
   ```powershell
   $env:DJANGO_SETTINGS_MODULE = "launch_points_web.settings.development"
   ```

4. **Create database migrations**:
   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser**:
   ```powershell
   python manage.py createsuperuser
   ```

6. **Collect static files**:
   ```powershell
   python manage.py collectstatic --noinput
   ```

7. **Run development server**:
   ```powershell
   python manage.py runserver
   ```

The application will be available at `http://127.0.0.1:8000/`

## Project Structure

```
launch_points_web/
├── manage.py
├── requirements_web.txt
├── launch_points_web/          # Main project package
│   ├── settings/
│   │   ├── base.py             # Base settings
│   │   ├── development.py      # Spatialite config
│   │   └── production.py       # MariaDB config
│   └── urls.py
├── core/                        # Core app
│   ├── models.py               # Database models
│   ├── admin.py                # Admin configuration
│   ├── views.py                # Views
│   └── urls.py
├── accounts/                    # Accounts app
├── static/                      # Static files
│   ├── css/
│   └── js/
├── templates/                   # HTML templates
├── media/                       # User-uploaded files
└── locale/                      # Translation files
```

## Settings

The project uses separate settings files:

- **Development**: `launch_points_web.settings.development` (Spatialite)
- **Production**: `launch_points_web.settings.production` (MariaDB)

Set the `DJANGO_SETTINGS_MODULE` environment variable to switch between them.

## Database Models

- **Region**: Map regions for navigation
- **TransportType**: Transport type configuration
- **POIType**: Point of interest types
- **RouteType**: Route type classification
- **Waterbody**: Waterbody picklist
- **PublicTransportStation**: Public transport stations
- **LaunchPoint**: Launch points for watercraft
- **PointOfInterest**: Points of interest
- **Waypoint**: Junction points
- **RouteSection**: Route sections over water
- **WalkPath**: Walking paths from stations to launch points
- **SavedRoute**: User-saved routes
- **Image**: Generic image model
- **Comment**: User comments
- **Rating**: Ratings within comments

## Next Steps

1. **Import legacy data**: Create and run the data migration script
2. **Set up API endpoints**: Implement GeoJSON and REST API endpoints
3. **Complete frontend**: Finish Leaflet map integration and HTMX interactions
4. **Add authentication**: Implement user registration and login
5. **Add editing features**: Create forms for editing content

## Development Notes

- The project uses Spatialite for development (no separate database server needed)
- For production, configure MariaDB connection in `settings/production.py`
- Translation files are in `locale/` directory
- Media files are stored in `media/images/` (unified storage)

## Troubleshooting

### GDAL/GEOS not found

If you get errors about GDAL or GEOS libraries:

1. Install the libraries (see Prerequisites)
2. Set environment variables:
   ```powershell
   $env:GDAL_LIBRARY_PATH = "C:\path\to\gdal.dll"
   $env:GEOS_LIBRARY_PATH = "C:\path\to\geos_c.dll"
   ```

### Database errors

- Make sure Spatialite is properly installed
- For MariaDB, ensure the database exists and credentials are correct

## License

See LICENSE file for details.

