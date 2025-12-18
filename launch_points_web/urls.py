"""
URL configuration for launch_points_web project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),  # Language switching (includes setlang/)
    path('admin/', admin.site.urls),
    # API endpoints should NOT have language prefix
    path('api/', include('core.api_urls')),
]

# Add language prefix to URLs (but not API)
urlpatterns += i18n_patterns(
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    prefix_default_language=False,  # Don't prefix default language (English)
)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

