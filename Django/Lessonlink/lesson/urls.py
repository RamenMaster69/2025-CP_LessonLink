from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.landing, name='landing'),
    path('registration_1/', views.registration_1, name='registration_1'),
    path('registration_2/', views.registration_2, name='registration_2'),
    path('registration_3/', views.registration_3, name='registration_3'),
    path('registration_4/', views.registration_4, name='registration_4'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('lesson_planner/', views.lesson_planner, name='lesson_planner'),
    path('draft/', views.draft, name='draft'),
    path('dep_dash/', views.Dep_Dash, name='Dep_Dash'),
    path('dep_faculty/', views.Dep_Faculty, name='Dep_Faculty'),
    path('task/', views.task, name='task'),
    path('schedule/', views.schedule, name='schedule'),
    path('dep_pending', views.Dep_Pending, name='Dep_Pending'),
    path('template/', views.template, name='template'),
]
# This is needed for development to serve media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)