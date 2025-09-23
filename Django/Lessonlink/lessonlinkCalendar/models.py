# lessonlinkCalendar/models.py
from django.db import models
from django.conf import settings

class CalendarActivity(models.Model):
    CATEGORY_CHOICES = [
        ('academic', 'Academic'),
        ('examination', 'Examination'),
        ('holiday', 'Holiday'),
        ('meeting', 'Meeting'),
        ('event', 'Event'),
        ('deadline', 'Deadline'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"