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

class task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')

    def __str__(self):
        return self.title

class schedule(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedules')
    class_name = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.class_name} - {self.user.first_name}"