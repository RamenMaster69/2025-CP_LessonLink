from django.utils import timezone
from datetime import timedelta
from .models import Notification
from lesson.models import LessonPlanSubmission, Task, Schedule

def check_task_due_soon():
    """Check for tasks due in 1 hour and create notifications"""
    from datetime import datetime, time
    
    now = timezone.now()
    one_hour_from_now = now + timedelta(hours=1)
    
    # Get tasks due within the next hour
    upcoming_tasks = Task.objects.filter(
        due_date=now.date(),
        due_time__gte=now.time(),
        due_time__lte=one_hour_from_now.time(),
        status='pending'
    )
    
    for task in upcoming_tasks:
        # Check if notification already exists for this task
        existing_notification = Notification.objects.filter(
            user=task.user,
            notification_type='task_due_soon',
            message__contains=task.title,
            created_at__date=now.date()
        ).exists()
        
        if not existing_notification:
            Notification.create_task_due_notification(task)

def check_upcoming_schedules():
    """Check for schedules happening today and create notifications"""
    today = timezone.now().date()
    
    # Get today's schedules
    today_schedules = Schedule.objects.filter(day=today.strftime('%A').lower())
    
    for schedule in today_schedules:
        # Check if notification already exists for this schedule today
        existing_notification = Notification.objects.filter(
            user=schedule.user,
            notification_type='upcoming_schedule',
            message__contains=schedule.subject,
            created_at__date=today
        ).exists()
        
        if not existing_notification:
            Notification.create_upcoming_schedule_notification(schedule.user, schedule)