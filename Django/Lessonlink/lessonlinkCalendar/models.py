# lessonlinkCalendar/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from lesson.models import SchoolRegistration

class CalendarActivity(models.Model):
    CATEGORY_CHOICES = [
        ('academic', 'Academic'),
        ('examination', 'Examination'),
        ('holiday', 'Holiday'),
        ('meeting', 'Meeting'),
        ('event', 'Event'),
        ('deadline', 'Deadline'),
        ('training', 'Training'),
        ('enrollment', 'Enrollment'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='calendar_activities')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    school = models.ForeignKey(SchoolRegistration, on_delete=models.CASCADE, null=True, blank=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        ordering = ['start_date', 'title']
        verbose_name_plural = "Calendar Activities"
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def clean(self):
        """Validate the activity data"""
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError('End date cannot be before start date.')
    
    def save(self, *args, **kwargs):
        """Auto-populate school and department from user if not set"""
        if not self.school and self.user.school:
            self.school = self.user.school
        if not self.department and self.user.department:
            self.department = self.user.department
        
        super().save(*args, **kwargs)
    
    @property
    def author(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    def is_admin_activity(self):
        return self.user.is_superuser
    
    def can_edit(self, request_user):
        """Check if user can edit this activity"""
        print(f"DEBUG can_edit: User {request_user.email} (role: {request_user.role}), Activity by {self.user.email} (admin: {self.user.is_superuser})")
        
        # Admin can edit everything
        if request_user.is_superuser or getattr(request_user, 'role', '') == 'Admin':
            print("  -> Admin can edit everything")
            return True
        
        # Department Head can only edit their own activities (not admin activities)
        if getattr(request_user, 'role', '') == 'Department Head':
            can_edit = (self.user.id == request_user.id) and not self.user.is_superuser
            print(f"  -> Department Head can edit: {can_edit}")
            return can_edit
        
        # Teacher CANNOT edit anything (read-only)
        if getattr(request_user, 'role', '') == 'Teacher':
            print("  -> Teacher cannot edit (read-only)")
            return False
        
        # Student Teacher CANNOT edit anything (read-only)
        if getattr(request_user, 'role', '') == 'Student Teacher':
            print("  -> Student Teacher cannot edit (read-only)")
            return False
        
        # Default: cannot edit
        print("  -> Default: cannot edit")
        return False
    
    def can_delete(self, request_user):
        """Check if user can delete this activity"""
        print(f"DEBUG can_delete: User {request_user.email} (role: {request_user.role}), Activity by {self.user.email} (admin: {self.user.is_superuser})")
        
        # Admin can delete everything
        if request_user.is_superuser or getattr(request_user, 'role', '') == 'Admin':
            print("  -> Admin can delete everything")
            return True
        
        # Department Head can only delete their own activities (not admin activities)
        if getattr(request_user, 'role', '') == 'Department Head':
            can_delete = (self.user.id == request_user.id) and not self.user.is_superuser
            print(f"  -> Department Head can delete: {can_delete}")
            return can_delete
        
        # Teacher CANNOT delete anything (read-only)
        if getattr(request_user, 'role', '') == 'Teacher':
            print("  -> Teacher cannot delete (read-only)")
            return False
        
        # Student Teacher CANNOT delete anything (read-only)
        if getattr(request_user, 'role', '') == 'Student Teacher':
            print("  -> Student Teacher cannot delete (read-only)")
            return False
        
        # Default: cannot delete
        print("  -> Default: cannot delete")
        return False


class ZamboangaEvent(models.Model):
    """Automatic annual Zamboanga events that work forever"""
    CATEGORY_CHOICES = [
        ('festival', 'Festival'),
        ('cultural', 'Cultural'),
        ('holiday', 'Holiday'),
        ('sports', 'Sports'),
        ('government', 'Government'),
        ('religious', 'Religious'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_month = models.PositiveIntegerField(help_text="Month (1-12)")
    start_day = models.PositiveIntegerField(help_text="Day of month (1-31)")
    duration_days = models.PositiveIntegerField(default=1, help_text="How many days the event lasts")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    location = models.CharField(max_length=300, default='Zamboanga City')
    organizer = models.CharField(max_length=200, blank=True)
    is_annual = models.BooleanField(default=True, help_text="Event repeats every year automatically")
    is_active = models.BooleanField(default=True, help_text="Show this event in the calendar")
    notes = models.TextField(blank=True, help_text="Additional information about the event")
    
    class Meta:
        ordering = ['start_month', 'start_day']
        verbose_name_plural = "Zamboanga Events"
    
    def __str__(self):
        return f"{self.title} (Annual)"
    
    def clean(self):
        """Validate the event data"""
        if self.start_month < 1 or self.start_month > 12:
            raise ValidationError('Start month must be between 1 and 12.')
        
        if self.start_day < 1 or self.start_day > 31:
            raise ValidationError('Start day must be between 1 and 31.')
        
        if self.duration_days < 1:
            raise ValidationError('Duration must be at least 1 day.')
    
    def get_dates_for_year(self, year=None):
        """Calculate actual dates for any given year"""
        if year is None:
            year = timezone.now().year
        
        try:
            start_date = date(year, self.start_month, self.start_day)
            end_date = start_date + timedelta(days=self.duration_days - 1)
            return start_date, end_date
        except ValueError as e:
            # Handle invalid dates (e.g., February 30)
            raise ValidationError(f"Invalid date combination: {e}")
    
    @property
    def next_occurrence(self):
        """Get the next occurrence of this event"""
        current_year = timezone.now().year
        start_date, end_date = self.get_dates_for_year(current_year)
        
        # If event has already passed this year, show next year
        if end_date < timezone.now().date():
            start_date, end_date = self.get_dates_for_year(current_year + 1)
        
        return start_date, end_date
    
    def save(self, *args, **kwargs):
        """Validate before saving"""
        self.clean()
        super().save(*args, **kwargs)