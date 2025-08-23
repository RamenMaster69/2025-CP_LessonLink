from django.contrib.auth.hashers import make_password, check_password
from django.db import models
from django.contrib.auth.models import User


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
