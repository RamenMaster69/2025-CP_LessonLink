from django.contrib.auth.hashers import make_password, check_password
from django.db import models

class User(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    dob = models.DateField()
    
    role = models.CharField(max_length=100)
    rank = models.CharField(max_length=100)
    
    department = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    affiliations = models.TextField(blank=True, null=True)

    # image = models.ImageField(null=True, blank=True, upload_to='images/') # Image field for user profile picture

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

DAY_CHOICES = [
    ('monday', 'Monday'),
    ('tuesday', 'Tuesday'),
    ('wednesday', 'Wednesday'),
    ('thursday', 'Thursday'),
    ('friday', 'Friday'),
]

TIME_CHOICES = [
    ('8:00 - 9:00 AM', '8:00 - 9:00 AM'),
    ('9:00 - 10:00 AM', '9:00 - 10:00 AM'),
    ('10:00 - 11:00 AM', '10:00 - 11:00 AM'),
    ('11:00 - 12:00 PM', '11:00 - 12:00 PM'),
    ('1:00 - 2:00 PM', '1:00 - 2:00 PM'),
    ('2:00 - 3:00 PM', '2:00 - 3:00 PM'),
    ('3:00 - 4:00 PM', '3:00 - 4:00 PM'),
    ('4:00 - 5:00 PM', '4:00 - 5:00 PM'),
]

class ClassSchedule(models.Model):
    subject = models.CharField(
        max_length=100,
        help_text="e.g. Mathematics, English, Science"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Brief description of the class"
    )
    day = models.CharField(
        max_length=10,
        choices=DAY_CHOICES,
        help_text="Day of the week for the class"
    )
    time = models.CharField(
        max_length=20,
        choices=TIME_CHOICES,
        help_text="Time slot for the class"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject} - {self.get_day_display()} {self.time}"

    class Meta:
        verbose_name = "Class Schedule"
        verbose_name_plural = "Class Schedules"
        ordering = ['day', 'time']
