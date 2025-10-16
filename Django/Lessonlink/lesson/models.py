from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator, EmailValidator
from datetime import datetime, date, time


class CustomUserManager(BaseUserManager):
    """Custom user manager that uses email instead of username"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with an email and password"""
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with an email and password"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        # Set default values for required fields if not provided
        extra_fields.setdefault('first_name', 'Admin')
        extra_fields.setdefault('last_name', 'User')
        extra_fields.setdefault('role', 'Department Head')
        extra_fields.setdefault('rank', 'Administrator')
        extra_fields.setdefault('department', 'Administration')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('Student Teacher', 'Student Teacher'),
        ('Teacher', 'Teacher'),
        ('Department Head', 'Department Head'),
        ('Admin', 'Admin'),
    ]

    username = None
    email = models.EmailField(unique=True)

    middle_name = models.CharField(max_length=100, blank=True, null=True)
    dob = models.DateField(null=True, blank=True)

    role = models.CharField(max_length=100, choices=ROLE_CHOICES)
    rank = models.CharField(max_length=100)

    department = models.CharField(max_length=100)

    # Instead of plain CharField, link to SchoolRegistration
    school = models.ForeignKey(
        "SchoolRegistration",  # reference your school model
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="users"
    )

    affiliations = models.TextField(blank=True, null=True)

    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        help_text="Profile picture for the user"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role', 'rank', 'department']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return ' '.join(parts).strip()

class AdminLog(models.Model):
    ACTION_CHOICES = [
        ('user_created', 'User Created'),
        ('user_modified', 'User Modified'),
        ('user_deactivated', 'User Deactivated'),
        ('role_changed', 'Role Changed'),
        ('lesson_approved', 'Lesson Approved'),
        ('lesson_flagged', 'Lesson Flagged'),
        ('password_reset', 'Password Reset'),
        ('account_unlocked', 'Account Unlocked'),
        ('school_admin_created', 'School Admin Created'), 
        ('school_admin_deactivated', 'School Admin Deactivated'),  
        ('school_admin_activated', 'School Admin Activated'),  
    ]
    
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_actions')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_actions_against')
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.admin.email} - {self.action} - {self.timestamp}"

class SystemSettings(models.Model):
    """System-wide settings that admins can configure"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.key


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
        verbose_name="Year Established",
        help_text="Year the institution was established"
    )

    password = models.CharField(
        max_length=128,
        verbose_name="Admin Password",
        help_text="Password for the school administrator account",
        null=True,
        blank=True
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
        from django.utils import timezone
        
        if not self.accuracy:
            raise ValidationError({'accuracy': 'You must certify the accuracy of information provided.'})
        
        if not self.terms:
            raise ValidationError({'terms': 'You must agree to the Terms of Service and Privacy Policy.'})
        
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
        self.status = 'approved'
        from django.utils import timezone
        self.processed_at = timezone.now()
        if processed_by_user:
            self.processed_by = processed_by_user
        self.save()
    
    def reject_registration(self, processed_by_user=None, reason=None):
        self.status = 'rejected'
        from django.utils import timezone
        self.processed_at = timezone.now()
        if processed_by_user:
            self.processed_by = processed_by_user
        if reason:
            self.admin_notes = reason
        self.save()
    
    def request_additional_info(self, processed_by_user=None, notes=None):
        self.status = 'needs_info'
        from django.utils import timezone
        self.processed_at = timezone.now()
        if processed_by_user:
            self.processed_by = processed_by_user
        if notes:
            self.admin_notes = notes
        self.save()


class SchoolAdmin(models.Model):
    """Model to manage school administrators for approved schools"""
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='school_admin_profile'
    )
    school = models.ForeignKey(
        SchoolRegistration, 
        on_delete=models.CASCADE, 
        related_name='admins'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_school_admins'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "School Admin"
        verbose_name_plural = "School Admins"
        indexes = [
            models.Index(fields=['school', 'is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.school.school_name}"

    @property
    def full_name(self):
        return self.user.get_full_name()

    @property
    def email(self):
        return self.user.email

    @property
    def username(self):
        return self.user.username

    def deactivate(self):
        """Deactivate the school admin"""
        self.is_active = False
        self.user.is_active = False
        self.user.save()
        self.save()

    def activate(self):
        """Activate the school admin"""
        self.is_active = True
        self.user.is_active = True
        self.user.save()
        self.save()


class LessonPlanSubmission(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted for Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_revision', 'Needs Revision'),
    ]
    
    lesson_plan = models.ForeignKey('lessonGenerator.LessonPlan', on_delete=models.CASCADE)
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_lesson_plans')
    submitted_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_lesson_plans')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submission_date = models.DateTimeField(auto_now_add=True)
    review_date = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-submission_date']
        constraints = [
            models.UniqueConstraint(
                fields=['lesson_plan', 'status'],
                condition=models.Q(status__in=['submitted', 'approved', 'needs_revision']),
                name='unique_active_submission'
            )
        ]
    
    def __str__(self):
        return f"{self.lesson_plan.title} - {self.get_status_display()}"
    
    def time_since_submission(self):
        """Return how long ago the lesson was submitted"""
        from django.utils import timezone
        now = timezone.now()
        diff = now - self.submission_date
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    
    def clean(self):
        """Validate that teacher and department head are in same school and department"""
        from django.core.exceptions import ValidationError
        
        if self.submitted_by and self.submitted_to:
            if self.submitted_by.school != self.submitted_to.school:
                raise ValidationError("Teacher and Department Head must be in the same school.")
            if self.submitted_by.department != self.submitted_to.department:
                raise ValidationError("Teacher and Department Head must be in the same department.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)