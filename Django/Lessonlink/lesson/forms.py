from django import forms
from .models import Schedule
import datetime
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class EducatorRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class EducatorRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User  # Use your custom User model
        fields = ['email', 'password1', 'password2']  # Remove 'username' since you don't use it

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove username field since your custom User model doesn't use it
        if 'username' in self.fields:
            del self.fields['username']

class SchoolAdminRegistrationForm(forms.Form):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        }),
        min_length=8
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists. Please choose a different email.")
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match.")
        
        return cleaned_data

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['title', 'day', 'start_time', 'end_time', 'instructor', 'color', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-gray-900', 'placeholder': 'e.g., System Integration'}),
            'day': forms.Select(attrs={'class': 'w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-gray-900'}),
            'start_time': forms.TimeInput(attrs={'class': 'w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-gray-900', 'type': 'time', 'min': '06:00', 'max': '19:00'}),
            'end_time': forms.TimeInput(attrs={'class': 'w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-gray-900', 'type': 'time', 'min': '06:00', 'max': '19:00'}),
            'instructor': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-gray-900', 'placeholder': 'e.g., Sir Ceed'}),
            'color': forms.TextInput(attrs={'class': 'hidden', 'id': 'event-color'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-3 border rounded-lg resize-none', 'rows': 3, 'placeholder': 'Optional notes or description'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        day = cleaned_data.get('day')
        user = self.instance.user if self.instance.pk else None
        
        if start_time and end_time:
            # Check if start time is before end time
            if start_time >= end_time:
                raise forms.ValidationError("End time must be after start time.")
            
            # Check if within working hours (6:00 AM - 7:00 PM)
            if start_time < datetime.time(6, 0) or end_time > datetime.time(19, 0):
                raise forms.ValidationError("Classes must be scheduled between 6:00 AM and 7:00 PM.")
            
            # Check for overlapping schedules
            if user and day:
                overlapping = Schedule.objects.filter(
                    user=user,
                    day=day,
                    start_time__lt=end_time,
                    end_time__gt=start_time
                ).exclude(pk=self.instance.pk if self.instance.pk else None)
                
                if overlapping.exists():
                    raise forms.ValidationError("This time slot overlaps with another class.")
        
        return cleaned_data