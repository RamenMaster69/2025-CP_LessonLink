from django.db import models
from django.conf import settings
from django.utils import timezone
from lesson.models import LessonPlanSubmission
from lessonGenerator.models import LessonPlan

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('draft_approved', 'Draft Approved'),
        ('draft_rejected', 'Draft Rejected'),
        ('task_due_soon', 'Task Due Soon'),
        ('upcoming_schedule', 'Upcoming Schedule'),
        ('lesson_submitted', 'Lesson Plan Submitted'),
        ('general', 'General Notification'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    
    # Related objects (optional - for linking notifications to specific content)
    lesson_plan = models.ForeignKey(LessonPlan, on_delete=models.CASCADE, null=True, blank=True)
    submission = models.ForeignKey(LessonPlanSubmission, on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.notification_type} - {self.title}"
    
    @classmethod
    def create_draft_status_notification(cls, submission, approved=True):
        """Create notification for draft approval/rejection"""
        if approved:
            notification_type = 'draft_approved'
            title = 'Lesson Plan Approved'
            message = f'Your lesson plan "{submission.lesson_plan.title}" has been approved.'
        else:
            notification_type = 'draft_rejected'
            title = 'Lesson Plan Needs Revision'
            message = f'Your lesson plan "{submission.lesson_plan.title}" needs revision.'
        
        return cls.objects.create(
            user=submission.submitted_by,
            notification_type=notification_type,
            title=title,
            message=message,
            submission=submission,
            lesson_plan=submission.lesson_plan
        )
    
    @classmethod
    def create_task_due_notification(cls, task):
        """Create notification for task due in 1 hour"""
        from django.utils import timezone
        from datetime import timedelta
        
        return cls.objects.create(
            user=task.user,
            notification_type='task_due_soon',
            title='Task Due Soon',
            message=f'Your task "{task.title}" is due in 1 hour.',
            created_at=timezone.now()
        )
    
    @classmethod
    def create_upcoming_schedule_notification(cls, user, schedule):
        """Create notification for upcoming schedule"""
        return cls.objects.create(
            user=user,
            notification_type='upcoming_schedule',
            title='Upcoming Class',
            message=f'You have "{schedule.subject}" scheduled for today at {schedule.time}.',
            created_at=timezone.now()
        )
    
    @classmethod
    def create_lesson_submitted_notification(cls, submission):
        """Create notification when someone submits a lesson plan"""
        return cls.objects.create(
            user=submission.submitted_to,
            notification_type='lesson_submitted',
            title='New Lesson Plan Submission',
            message=f'{submission.submitted_by.full_name} submitted a lesson plan for review: "{submission.lesson_plan.title}"',
            submission=submission,
            lesson_plan=submission.lesson_plan
        )
