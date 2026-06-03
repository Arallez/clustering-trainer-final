from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core.admin_site import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', include(('apps.core.urls', 'core'), namespace='core')),
    path('materials/', include('apps.materials.urls', namespace='materials')),
    path('tasks/', include('apps.tasks.urls', namespace='tasks')),
    path('encyclopedia/', include('apps.encyclopedia.urls', namespace='encyclopedia')),
    path('simulator/', include('apps.simulator.urls', namespace='simulator')),
    path('testing/', include('apps.testing.urls', namespace='testing')),
]

if settings.DEBUG:
    # Use default /media/ prefix in case settings doesn't have it initialized yet during reload
    media_url = getattr(settings, 'MEDIA_URL', '/media/')
    media_root = getattr(settings, 'MEDIA_ROOT', settings.BASE_DIR / 'media')
    urlpatterns += static(media_url, document_root=media_root)
