# lessonlinkCalendar/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
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