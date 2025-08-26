from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import datetime, date, time


class User(models.Model):
    ROLE = [
        ('student_teacher', 'Student Teacher'),
        ('teacher', 'Teacher'),
        ('department_head', 'Department Head'),
    ]
    
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    dob = models.DateField()
    
    role = models.CharField(max_length=100, choices=ROLE)
    rank = models.CharField(max_length=100)
    
    department = models.CharField(max_length=100)
    affiliations = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # Hash password if it's not already hashed
        if not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    
    def check_password(self, raw_password):
        """Check if the provided raw password matches the stored hashed password"""
        return check_password(raw_password, self.password)

class Schedule(models.Model):
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
    ]
    
    TIME_SLOTS = [
        ('8:00 - 9:00 AM', '8:00 - 9:00 AM'),
        ('9:00 - 10:00 AM', '9:00 - 10:00 AM'),
        ('10:00 - 11:00 AM', '10:00 - 11:00 AM'),
        ('11:00 - 12:00 PM', '11:00 - 12:00 PM'),
        ('1:00 - 2:00 PM', '1:00 - 2:00 PM'),
        ('2:00 - 3:00 PM', '2:00 - 3:00 PM'),
        ('3:00 - 4:00 PM', '3:00 - 4:00 PM'),
        ('4:00 - 5:00 PM', '4:00 - 5:00 PM'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    time = models.CharField(max_length=20, choices=TIME_SLOTS)
    
    class Meta:
        unique_together = ['user', 'day', 'time']
    
    def __str__(self):
        return f"{self.subject} on {self.day} at {self.time}"

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateField(blank=True, null=True)
    due_time = models.TimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def is_overdue(self):
        if self.due_date and self.status == 'pending':
            # make sure due_date is a date
            due_date = self._get_date(self.due_date)
            return timezone.now().date() > due_date
        return False

    def formatted_due_date(self):
        if self.due_date:
            due_date = self._get_date(self.due_date)
            return due_date.strftime('%Y-%m-%d')
        return None

    def display_due_date(self):
        if not self.due_date:
            return "No due date"
        
        due_date = self._get_date(self.due_date)
        today = timezone.now().date()
        tomorrow = today + timezone.timedelta(days=1)
        
        if due_date == today:
            return "Today"
        elif due_date == tomorrow:
            return "Tomorrow"
        else:
            return due_date.strftime('%A, %B %d')

    def display_due_datetime(self):
        if not self.due_date:
            return "No due date"
        
        due_date = self._get_date(self.due_date)
        date_str = self.display_due_date()
        
        if self.due_time:
            due_time = self._get_time(self.due_time)
            time_str = due_time.strftime('%I:%M %p')
            return f"{date_str}, {time_str}"
        
        return date_str

    # --- helpers to safely parse strings ---
    def _get_date(self, value):
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d").date()
        return value

    def _get_time(self, value):
        if isinstance(value, str):
            return datetime.strptime(value, "%H:%M").time()
        return value

class TaskNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('due_soon', 'Due Soon'),
        ('overdue', 'Overdue'),
        ('completed', 'Completed'),
        ('new', 'New Task'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} notification for {self.task.title}"