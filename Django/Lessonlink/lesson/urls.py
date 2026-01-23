from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import landing, dep_template, teach_template, calendar, admin_calendar, dep_calendar
from .views import registration_1, registration_2, registration_3, registration_4, org_reg_1
from .views import login_view, logout_view
from .views import lesson_planner, lesson_plan
from .views import dashboard, profile, ScheduleViewSet, draft, task, schedule
from .views import Dep_Dash, Dep_Faculty, Dep_Pending
from .views import st_dash
from .views import admin_dashboard
from django.contrib import admin
from . import views 
from django.conf import settings
from django.conf.urls.static import static

# Import the new task API views
from .views import (
    add_task_api, update_task_status_api, delete_task_api,
    get_notifications_api, mark_notification_read_api
)

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
    
    # ======================================================
    # SCHOOL REGISTRATION URL (ADD THIS LINE)
    # ======================================================
    path('register/school/', org_reg_1, name='school_registration'),  # ADD THIS
    
    # You already have org_reg_1, but it's better to have a clear name
    path('org_reg_1/', org_reg_1, name='org_reg_1'),  # Keep this for compatibility
    path('school-registration/', views.org_reg_1, name='org_reg_1'),

    
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('profile/', profile, name='profile'),
    path('upload-profile-picture/', views.upload_profile_picture, name='upload_profile_picture'),
    path('lesson_planner/', lesson_planner, name='lesson_planner'),
    path('lesson_plan/', lesson_plan, name='lesson_plan'),
    path('draft/', draft, name='draft'),
    path('dep_dash/', Dep_Dash, name='Dep_Dash'),
    path('dep_faculty/', Dep_Faculty, name='Dep_Faculty'),
    path('dep_exemplar/', views.Dep_exemplar, name='Dep_exemplar'),
    path('task/', task, name='task'),
    path('schedule/', schedule, name='schedule'),
    path('dep_pending/', Dep_Pending, name='Dep_Pending'),
    path('dep_calendar/', dep_calendar, name='dep_calendar'),
    path('dep_template/', dep_template, name='dep_template'),
    path('teach_template/', teach_template, name='teach_template'),
    path('calendar-view/', calendar, name='calendar'),
    path('st_dash/', st_dash, name='st_dash'),
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin_calendar/', admin_calendar, name='admin_calendar'),
    path('submit-lesson-plan/<int:lesson_plan_id>/', views.submit_lesson_plan, name='submit_lesson_plan'),
    path('review-lesson-plan/<int:submission_id>/', views.review_lesson_plan, name='review_lesson_plan'),
    path('lesson-plan-detail/<int:submission_id>/', views.lesson_plan_detail, name='lesson_plan_detail'),
    path('faculty-management/', views.admin_dep_faculty_management, name='admin_faculty_management'),
    path('teacher_calendar/', views.teacher_calendar, name='teacher_calendar'),
    path('admin/school-registrations/', views.admin_school_registrations, name='admin_school_registrations'),

    # Admin URLs
    path('admin/user-management/', views.admin_user_management, name='admin_user_management'),
    path('admin/edit-user/<int:user_id>/', views.admin_edit_user, name='admin_edit_user'),
    path('admin/reset-password/<int:user_id>/', views.admin_reset_password, name='admin_reset_password'),
    path('admin/system-reports/', views.admin_system_reports, name='admin_system_reports'),
    path('admin/lesson-monitoring/', views.admin_lesson_monitoring, name='admin_lesson_monitoring'),
    path('admin/export-reports/<str:format_type>/', views.admin_export_reports, name='admin_export_reports'),

    # Calendar API URLs
    path('calendar-api/', include(('lessonlinkCalendar.urls', 'lessonlinkCalendar'), namespace='lessonlinkcalendar_api')),

    # ======================================================
    # SUPER USER SCHOOL APPROVAL URLs
    # ======================================================
    path('super-user/', views.super_user_dashboard, name='super_user_dashboard'),
    path('super-user/approve/<int:school_id>/', views.approve_school, name='approve_school'),
    path('super-user/reject/<int:school_id>/', views.reject_school, name='reject_school'),
    path('super-user/school/<int:school_id>/', views.super_user_school_detail, name='super_user_school_detail'),

    # AJAX validation endpoint
    path('validate-school-id/', views.validate_school_id_ajax, name='validate_school_id_ajax'),
    
    # School admin management URLs
    path('school/<int:school_id>/register-admin/', views.register_school_admin, name='register_school_admin'),
    path('school/<int:school_id>/admins/', views.school_admin_list, name='school_admin_list'),
    path('school-admin/<int:admin_id>/deactivate/', views.deactivate_school_admin, name='deactivate_school_admin'),
    path('school-admin/<int:admin_id>/activate/', views.activate_school_admin, name='activate_school_admin'),

    # Exemplar URLs
    path('dep_exemplar/', views.Dep_exemplar, name='Dep_exemplar'),
    path('api/exemplars/upload/', views.upload_exemplar, name='upload_exemplar'),
    path('api/exemplars/', views.get_exemplars, name='get_exemplars'),
    path('api/exemplars/<int:exemplar_id>/delete/', views.delete_exemplar, name='delete_exemplar'),
    path('api/exemplars/<int:exemplar_id>/text/', views.get_exemplar_text, name='get_exemplar_text'),
    path('api/exemplars/department/', views.get_department_exemplars, name='get_department_exemplars'),
    
    # Teacher/Student URLs
    path('api/get-teachers/', views.get_teachers_by_department, name='get_teachers'),
    path('teacher/my-students/', views.teacher_student_list, name='teacher_student_list'),
    path('teacher/student/<int:student_id>/', views.teacher_student_detail, name='teacher_student_detail'),
    path('teacher/students/<int:student_id>/approval/', views.update_student_approval, name='update_student_approval'),
    
    # Concern URLs
    path('api/student-concerns/submit/', views.submit_student_concern, name='submit_student_concern'),
    path('teacher/students/<int:student_id>/concerns/', views.get_student_concerns, name='get_student_concerns'),
    path('teacher/concerns/<int:concern_id>/resolve/', views.resolve_student_concern, name='resolve_student_concern'),
    path('teacher/concerns/<int:concern_id>/', views.get_concern_detail, name='get_concern_detail'),

    # Teacher review URLs
    path('teacher/reviews/', views.supervising_teacher_reviews, name='supervising_teacher_reviews'),
    path('teacher/review-student-lesson/<int:submission_id>/', views.review_student_lesson_plan, name='review_student_lesson_plan'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)