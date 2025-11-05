from django import forms
from .models import UploadedFile, LessonPlan
import os

class FileUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedFile
        fields = ['file']
        
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (5MB limit)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File too large. Maximum size is 5MB.")
            
            # Check file extensions
            valid_extensions = ['.txt', '.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError("Unsupported file format.")
                
        return file

class LessonPlanFromFileForm(forms.ModelForm):
    """Form for creating lesson plan from extracted text"""
    class Meta:
        model = LessonPlan
        fields = ['title', 'subject', 'grade_level', 'duration', 'population']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'grade_level': forms.TextInput(attrs={'class': 'form-control'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'population': forms.NumberInput(attrs={'class': 'form-control'}),
        }