# lessonlinkCalendar/urls.py
from django.urls import path
from . import views

app_name = 'lessonlinkCalendar'

urlpatterns = [
    path('activities/', views.get_calendar_activities, name='get_calendar_activities'),
    path('activities/add/', views.add_calendar_activity, name='add_calendar_activity'),
    path('activities/delete/<int:activity_id>/', views.delete_calendar_activity, name='delete_calendar_activity'),
]