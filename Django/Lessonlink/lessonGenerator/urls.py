# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Existing URLs
    path('lesson_ai/', views.lesson_ai, name='lesson_ai'),
    path('generate-lesson-plan/', views.generate_lesson_plan, name='generate_lesson_plan'),
    path('lesson-plan-result/', views.lesson_plan_result, name='lesson_plan_result'),
    path('save-lesson-plan/', views.save_lesson_plan, name='save_lesson_plan'),
    path('drafts/', views.draft_list, name='draft_list'),
    path('drafts/department-head/', views.department_head_drafts, name='department_head_drafts'),
    path('drafts/<int:draft_id>/edit/', views.edit_draft, name='edit_draft'),
    path('drafts/<int:draft_id>/view/', views.view_draft, name='view_draft'),
    path('regenerate-lesson-content/', views.regenerate_lesson_content, name='regenerate_lesson_content'),
    path('get-ai-suggestions/', views.get_ai_suggestions, name='get_ai_suggestions'),
    
    # NEW FILE UPLOAD URLs
    path('upload/', views.upload_file, name='upload_file'),
    path('files/', views.file_list, name='file_list'),
    path('file/<int:file_id>/', views.file_detail, name='file_detail'),
    path('file/<int:file_id>/delete/', views.delete_file, name='delete_file'),
    path('file/<int:file_id>/create-lesson/', views.create_lesson_from_file, name='create_lesson_from_file'),
    path('lesson/<int:lesson_id>/generate-from-file/', views.generate_from_file, name='generate_from_file'),
    path('api/upload/', views.api_upload, name='api_upload'),
]