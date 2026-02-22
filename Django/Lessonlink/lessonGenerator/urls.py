# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('lesson_ai/', views.lesson_ai, name='lesson_ai'),
    path('lesson_ai_weekly', views.lesson_ai_weekly, name='lesson_ai_weekly'),
    path('generate-lesson-plan/', views.generate_lesson_plan, name='generate_lesson_plan'),
    path('lesson-plan-result/', views.lesson_plan_result, name='lesson_plan_result'),
    path('save-lesson-plan/', views.save_lesson_plan, name='save_lesson_plan'),
    path('drafts/', views.draft_list, name='draft_list'),
    path('drafts/department-head/', views.department_head_drafts, name='department_head_drafts'),
    path('drafts/<int:draft_id>/edit/', views.edit_draft, name='edit_draft'),
    path('drafts/<int:draft_id>/view/', views.view_draft, name='view_draft'),
    path('drafts/<int:draft_id>/delete/', views.delete_draft, name='delete_draft'),
    path('regenerate-lesson-content/', views.regenerate_lesson_content, name='regenerate_lesson_content'),
    path('get-ai-suggestions/', views.get_ai_suggestions, name='get_ai_suggestions'),
    path('check-exemplar-compatibility/', views.check_exemplar_compatibility, name='check_exemplar_compatibility'),
    path('view_weekly_draft/', views.view_weekly_draft, name='view_weekly_draft'),
]