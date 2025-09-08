from django.urls import path
from . import views

urlpatterns = [
    path('index/', views.index, name='index'),
    path('generate-lesson-plan/', views.generate_lesson_plan, name='generate_lesson_plan'),
    path('lesson-plan-result/', views.lesson_plan_result, name='lesson_plan_result'),
]