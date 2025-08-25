from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ScheduleViewSet, landing, registration_1, registration_2, registration_3
from .views import registration_4, login_view, logout_view, dashboard, profile
from .views import lesson_planner, lesson_plan, draft, Dep_Dash, Dep_Faculty, task, schedule  # Add schedule here
from .views import Dep_Pending, template, st_dash
from django.conf import settings
from django.conf.urls.static import static

# REST Framework router
router = DefaultRouter()
router.register(r'schedules', ScheduleViewSet, basename='schedule')

urlpatterns = [
    # REST API endpoints
    path('api/', include(router.urls)),
    
    # Regular Django views
    path('', landing, name='landing'),
    path('registration_1/', registration_1, name='registration_1'),
    path('registration_2/', registration_2, name='registration_2'),
    path('registration_3/', registration_3, name='registration_3'),
    path('registration_4/', registration_4, name='registration_4'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('profile/', profile, name='profile'),
    path('lesson_planner/', lesson_planner, name='lesson_planner'),
    path('lesson_plan/', lesson_plan, name='lesson_plan'),  # Added alternative path
    path('draft/', draft, name='draft'),
    path('dep_dash/', Dep_Dash, name='Dep_Dash'),
    path('dep_faculty/', Dep_Faculty, name='Dep_Faculty'),
    path('task/', task, name='task'),
    path('schedule/', schedule, name='schedule'),  # Add this line
    path('dep_pending/', Dep_Pending, name='Dep_Pending'),
    path('template/', template, name='template'),
    path('st_dash/', st_dash, name='st_dash'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)