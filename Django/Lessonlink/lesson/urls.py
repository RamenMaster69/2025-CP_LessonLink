from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('register_1/', views.registration_1, name='registration_1'),
    path('register_2/', views.registration_2, name='registration_2'),
    path('register_3/', views.registration_3, name='registration_3'),
    path('register_4/', views.registration_4, name='registration_4'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('lesson_planner/', views.lesson_planner, name='lesson_planner'),
]