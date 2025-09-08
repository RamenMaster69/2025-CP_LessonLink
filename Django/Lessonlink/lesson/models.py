from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import RegexValidator, EmailValidator
from datetime import datetime, date, time


class User(models.Model):
    ROLE = [
        ('Student Teacher', 'Student Teacher'),
        ('Teacher', 'Teacher'),
        ('Department Head', 'Department Head'),
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
    
    # Add this field for profile pictures
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', 
        null=True, 
        blank=True,
        help_text="Profile picture for the user"
    )

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


class SchoolRegistration(models.Model):
    """Enhanced model to store comprehensive school registration data"""
    
    # Status choices for admin management
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_info', 'Needs Additional Information'),
    ]
    
    REGION_CHOICES = [
        ('Region IX - Zamboanga Peninsula', 'Region IX - Zamboanga Peninsula'),
        ('BARMM', 'BARMM'),
        # Add more regions as needed
        ('NCR', 'National Capital Region'),
        ('CAR', 'Cordillera Administrative Region'),
        ('Region I - Ilocos Region', 'Region I - Ilocos Region'),
        ('Region II - Cagayan Valley', 'Region II - Cagayan Valley'),
        ('Region III - Central Luzon', 'Region III - Central Luzon'),
        ('Region IV-A - CALABARZON', 'Region IV-A - CALABARZON'),
        ('Region IV-B - MIMAROPA', 'Region IV-B - MIMAROPA'),
        ('Region V - Bicol Region', 'Region V - Bicol Region'),
        ('Region VI - Western Visayas', 'Region VI - Western Visayas'),
        ('Region VII - Central Visayas', 'Region VII - Central Visayas'),
        ('Region VIII - Eastern Visayas', 'Region VIII - Eastern Visayas'),
        ('Region X - Northern Mindanao', 'Region X - Northern Mindanao'),
        ('Region XI - Davao Region', 'Region XI - Davao Region'),
        ('Region XII - SOCCSKSARGEN', 'Region XII - SOCCSKSARGEN'),
        ('Region XIII - Caraga', 'Region XIII - Caraga'),
    ]
    
    # Institution Details
    school_name = models.CharField(
        max_length=255,
        verbose_name="Official School Name",
        help_text="Complete official name of the institution"
    )
    
    school_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="School ID / DepEd Code",
        help_text="12-digit DepEd registration code or school identifier"
    )
    
    year_established = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Year Established",
        help_text="Year the institution was established"
    )
    
    # Contact Information
    address = models.TextField(
        verbose_name="Complete Address",
        help_text="Street, Barangay, City/Municipality"
    )
    
    province = models.CharField(
        max_length=100,
        verbose_name="Province"
    )
    
    region = models.CharField(
        max_length=100,
        choices=REGION_CHOICES,
        verbose_name="Region"
    )
    
    phone_number = models.CharField(
        max_length=20,
        verbose_name="Phone Number",
        help_text="Main contact phone number"
    )
    
    email = models.EmailField(
        verbose_name="Email Address",
        help_text="Official school email address"
    )
    
    website = models.URLField(
        blank=True,
        null=True,
        verbose_name="Website",
        help_text="School's official website"
    )
    
    facebook_page = models.URLField(
        blank=True,
        null=True,
        verbose_name="Facebook Page",
        help_text="School's official Facebook page"
    )
    
    # Administrative Contact
    contact_person = models.CharField(
        max_length=255,
        verbose_name="Contact Person Name",
        help_text="Primary contact person for system administration"
    )
    
    position = models.CharField(
        max_length=100,
        verbose_name="Position/Title",
        help_text="Job title of the contact person"
    )
    
    contact_email = models.EmailField(
        verbose_name="Contact Email",
        help_text="Email address of the contact person"
    )
    
    contact_phone = models.CharField(
        max_length=20,
        verbose_name="Contact Phone",
        help_text="Phone number of the contact person"
    )
    
    # File uploads (optional)
    certificate_file = models.FileField(
        upload_to="school_certificates/",
        blank=True,
        null=True,
        verbose_name="School Certificate",
        help_text="Upload school registration certificate or similar document"
    )
    
    # Agreement fields
    accuracy = models.BooleanField(
        default=False,
        verbose_name="Information Accuracy Certification",
        help_text="Certifies that all information provided is accurate and complete"
    )
    
    terms = models.BooleanField(
        default=False,
        verbose_name="Terms and Privacy Agreement",
        help_text="Agreement to Terms of Service and Privacy Policy"
    )
    
    communications = models.BooleanField(
        default=False,
        verbose_name="Communications Consent",
        help_text="Consent to receive updates about platform features via email"
    )
    
    # Administrative fields
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Registration Status"
    )
    
    admin_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Admin Notes",
        help_text="Internal notes for administrators"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Registration Date"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Last Updated"
    )
    
    processed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Processing Date",
        help_text="Date when the registration was processed"
    )
    
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Processed By",
        help_text="Administrator who processed this registration"
    )
    
    class Meta:
        verbose_name = "School Registration"
        verbose_name_plural = "School Registrations"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['school_id']),
        ]
    
    def __str__(self):
        return f"{self.school_name} ({self.school_id}) - {self.get_status_display()}"
    
    def clean(self):
        """Custom validation"""
        from django.core.exceptions import ValidationError
        
        # Validate required agreements
        if not self.accuracy:
            raise ValidationError({'accuracy': 'You must certify the accuracy of information provided.'})
        
        if not self.terms:
            raise ValidationError({'terms': 'You must agree to the Terms of Service and Privacy Policy.'})
        
        # Validate year established
        if self.year_established:
            current_year = timezone.now().year
            if self.year_established > current_year:
                raise ValidationError({'year_established': 'Year established cannot be in the future.'})
            if self.year_established < 1800:
                raise ValidationError({'year_established': 'Please enter a valid year.'})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def is_rejected(self):
        return self.status == 'rejected'
    
    def approve_registration(self, processed_by_user=None):
        """Approve the school registration"""
        self.status = 'approved'
        self.processed_at = timezone.now()
        if processed_by_user:
            self.processed_by = processed_by_user
        self.save()
    
    def reject_registration(self, processed_by_user=None, reason=None):
        """Reject the school registration"""
        self.status = 'rejected'
        self.processed_at = timezone.now()
        if processed_by_user:
            self.processed_by = processed_by_user
        if reason:
            self.admin_notes = reason
        self.save()
    
    def request_additional_info(self, processed_by_user=None, notes=None):
        """Request additional information"""
        self.status = 'needs_info'
        self.processed_at = timezone.now()
        if processed_by_user:
            self.processed_by = processed_by_user
        if notes:
            self.admin_notes = notes
        self.save()