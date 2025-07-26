from django.db import models
from django.contrib.auth.hashers import make_password

class User(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)  # Made optional
    last_name = models.CharField(max_length=100)
    dob = models.DateField()
    
    role = models.CharField(max_length=100)  # Keep required
    rank = models.CharField(max_length=100)  # Keep required
    
    department = models.CharField(max_length=100)  # Keep required
    specialization = models.CharField(max_length=100)  # Keep required
    affiliations = models.TextField(blank=True, null=True)  # Made optional

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # Hash password if it's not already hashed
        if not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)