from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import landing, dep_template, teach_template, calendar, admin_calendar
from .views import registration_1, registration_2, registration_3, registration_4, org_reg_1
from .views import login_view, logout_view
from .views import lesson_planner, lesson_plan
from .views import dashboard, profile, ScheduleViewSet, draft, task, schedule
from .views import Dep_Dash, Dep_Faculty, Dep_Pending
from .views import st_dash

# Import the new task API views
from .views import (
    add_task_api, update_task_status_api, delete_task_api,
    get_notifications_api, mark_notification_read_api
)
from django.conf import settings
from django.conf.urls.static import static
from . import views

# REST Framework router
router = DefaultRouter()
router.register(r'schedules', ScheduleViewSet, basename='schedule')

urlpatterns = [
    # REST API endpoints
    path('api/', include(router.urls)),
    
    # Task API endpoints
    path('api/tasks/add/', add_task_api, name='add_task_api'),
    path('api/tasks/update-status/<int:task_id>/', update_task_status_api, name='update_task_status_api'),
    path('api/tasks/delete/<int:task_id>/', delete_task_api, name='delete_task_api'),
    path('api/notifications/', get_notifications_api, name='get_notifications_api'),
    path('api/notifications/mark-read/<int:notification_id>/', mark_notification_read_api, name='mark_notification_read_api'),
    
    # Regular Django views
    path('', landing, name='landing'),
    path('registration_1/', registration_1, name='registration_1'),
    path('registration_2/', registration_2, name='registration_2'),
    path('registration_3/', registration_3, name='registration_3'),
    path('registration_4/', registration_4, name='registration_4'),
    path('org_reg_1/', org_reg_1, name='org_reg_1'),
    # path('school_registration/', school_registration, name='school_registration'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('profile/', profile, name='profile'),
    path('lesson_planner/', lesson_planner, name='lesson_planner'),
    path('lesson_plan/', lesson_plan, name='lesson_plan'),
    path('draft/', draft, name='draft'),
    path('dep_dash/', Dep_Dash, name='Dep_Dash'),
    path('dep_faculty/', Dep_Faculty, name='Dep_Faculty'),
    path('task/', task, name='task'),
    path('schedule/', schedule, name='schedule'),
    path('dep_pending/', Dep_Pending, name='Dep_Pending'),
    path('dep_template/', dep_template, name='dep_template'),
    path('teach_template/', teach_template, name='teach_template'),
    path('calendar/', calendar, name='calendar'),
    path('st_dash/', st_dash, name='st_dash'),
    path('admin_calendar/', admin_calendar, name='admin_calendar'),


    # path('upload-profile-picture/', upload_profile_picture, name='upload_profile_picture'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
