# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('lesson_ai/', views.lesson_ai, name='lesson_ai'),
    path('generate-lesson-plan/', views.generate_lesson_plan, name='generate_lesson_plan'),
    path('lesson-plan-result/', views.lesson_plan_result, name='lesson_plan_result'),
    path('save-lesson-plan/', views.save_lesson_plan, name='save_lesson_plan'),
    path('drafts/', views.draft_list, name='draft_list'),
    path('drafts/department-head/', views.department_head_drafts, name='department_head_drafts'),  # New
    path('drafts/<int:draft_id>/edit/', views.edit_draft, name='edit_draft'),
    path('regenerate-lesson-content/', views.regenerate_lesson_content, name='regenerate_lesson_content'),
    path('drafts/<int:draft_id>/view/', views.view_draft, name='view_draft'),
]