from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('registration_1/', views.registration_1, name='registration_1'),
    path('registration_2/', views.registration_2, name='registration_2'),
    path('registration_3/', views.registration_3, name='registration_3'),
    path('registration_4/', views.registration_4, name='registration_4'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('lesson_planner/', views.lesson_planner, name='lesson_planner'),
    path('draft/', views.draft, name='draft'),
]