from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendar_view, name='calendar_view'),
    path('api/activities/', views.activities_api, name='activities_api'),
    path('api/activities/<int:activity_id>/', views.delete_activity, name='delete_activity'),
]