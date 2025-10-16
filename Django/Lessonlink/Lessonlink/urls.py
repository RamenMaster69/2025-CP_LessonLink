from django.contrib import admin
from django.urls import path, include
from . import settings
from django.conf.urls.static import static

urlpatterns = [
    path('ombre/', admin.site.urls),
    path('', include('lesson.urls')),  # Include the lesson app URLs
    path('', include('lessonGenerator.urls')),
    # path('calendar/', include('lessonlinkCalendar.urls')),
    path('calendar/', include(('lessonlinkCalendar.urls', 'lessonlinkCalendar'), namespace='lessonlinkcalendar_main')),
     path('notifications/', include('lessonlinkNotif.urls')),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # Serve media files during development
