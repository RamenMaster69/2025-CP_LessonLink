from django.urls import path
from . import views

urlpatterns = [
    path('lesson_ai/', views.lesson_ai, name='lesson_ai'),
    path('generate-lesson-plan/', views.generate_lesson_plan, name='generate_lesson_plan'),
    path('lesson-plan-result/', views.lesson_plan_result, name='lesson_plan_result'),
]