# models.py
import re  # ✅ Added this
from django.db import models
from django.conf import settings  # ✅ Changed from django.contrib.auth.models import User


class LessonPlan(models.Model):
    DRAFT = 'draft'
    FINAL = 'final'
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (FINAL, 'Final'),
    ]

    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=100)
    grade_level = models.CharField(max_length=50)
    quarter = models.CharField(max_length=50, blank=True)
    duration = models.IntegerField()  # in minutes
    population = models.IntegerField()  # number of students
    learning_objectives = models.TextField()
    subject_matter = models.TextField()
    materials_needed = models.TextField()
    introduction = models.TextField()
    instruction = models.TextField()
    application = models.TextField()
    evaluation = models.TextField()
    assessment = models.TextField()
    generated_content = models.TextField()  # AI-generated content
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # ✅ Changed from User to settings.AUTH_USER_MODEL
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject} - {self.grade_level} - {self.title}"

    def parse_generated_content(self):
        """Parse the AI-generated content into sections and subsections"""
        sections = {}
        content = self.generated_content

        # Define patterns for each main section
        patterns = {
            'metadata': r'## Metadata\s*\n(.*?)(?=##|$)',
            'learning_objectives': r'## Learning Objectives\s*\n(.*?)(?=##|$)',
            'subject_matter': r'## Subject Matter\s*\n(.*?)(?=##|$)',
            'materials_needed': r'## Materials Needed\s*\n(.*?)(?=##|$)',
            'lesson_procedure': r'## Lesson Procedure\s*\n(.*?)(?=##|$)',
            'differentiation': r'## Differentiation\s*\n(.*?)(?=##|$)',
        }

        for section, pattern in patterns.items():
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                sections[section] = match.group(1).strip()
            else:
                sections[section] = ""

        # Parse Lesson Procedure subsections
        lesson_procedure = sections.get('lesson_procedure', '')
        procedure_subsections = {
            'introduction': r'### A\. Introduction\s*\(([^)]+)\)\s*\n(.*?)(?=###|$)',
            'instruction': r'### B\. Instruction/Direct Teaching\s*\(([^)]+)\)\s*\n(.*?)(?=###|$)',
            'application': r'### C\. Guided Practice/Application\s*\(([^)]+)\)\s*\n(.*?)(?=###|$)',
            'evaluation': r'### D\. Independent Practice/Evaluation\s*\(([^)]+)\)\s*\n(.*?)(?=###|$)',
            'assessment': r'### E\. Assessment\s*\(([^)]+)\)\s*\n(.*?)(?=###|$)',
        }

        procedure_data = {}
        for subsection, pattern in procedure_subsections.items():
            match = re.search(pattern, lesson_procedure, re.DOTALL | re.IGNORECASE)
            if match:
                procedure_data[subsection] = {
                    'time': match.group(1).strip(),
                    'content': match.group(2).strip()
                }
            else:
                procedure_data[subsection] = {'time': '', 'content': ''}

        sections['procedure_subsections'] = procedure_data

        # Parse Metadata fields
        metadata = sections.get('metadata', '')
        metadata_patterns = {
            'subject': r'\*\*Subject:\*\*\s*([^\n]+)',
            'grade_level': r'\*\*Grade Level:\*\*\s*([^\n]+)',
            'quarter': r'\*\*Quarter:\*\*\s*([^\n]+)',
            'duration': r'\*\*Duration:\*\*\s*([^\n]+)',
            'class_size': r'\*\*Class Size:\*\*\s*([^\n]+)',
        }

        metadata_data = {}
        for field, pattern in metadata_patterns.items():
            match = re.search(pattern, metadata, re.IGNORECASE)
            if match:
                metadata_data[field] = match.group(1).strip()
            else:
                metadata_data[field] = ""

        sections['metadata_fields'] = metadata_data

        # Parse Learning Objectives as list items
        objectives = sections.get('learning_objectives', '')
        objectives_list = re.findall(r'\*\s*(.*?)(?=\n\*|\n\n|$)', objectives, re.DOTALL)
        sections['learning_objectives_list'] = [obj.strip() for obj in objectives_list if obj.strip()]

        # Parse Materials Needed as list items
        materials = sections.get('materials_needed', '')
        materials_list = re.findall(r'\*\s*(.*?)(?=\n\*|\n\n|$)', materials, re.DOTALL)
        sections['materials_list'] = [mat.strip() for mat in materials_list if mat.strip()]

        # Parse Differentiation subsections
        differentiation = sections.get('differentiation', '')
        diff_subsections = {
            'support': r'\*\*Support for Struggling Learners:\*\*\s*(.*?)(?=\*\*|$)',
            'extension': r'\*\*Extension for Advanced Learners:\*\*\s*(.*?)(?=\*\*|$)',
        }

        diff_data = {}
        for subsection, pattern in diff_subsections.items():
            match = re.search(pattern, differentiation, re.DOTALL | re.IGNORECASE)
            if match:
                items = re.findall(r'\*\s*(.*?)(?=\n\*|\n\n|$)', match.group(1), re.DOTALL)
                diff_data[subsection] = [item.strip() for item in items if item.strip()]
            else:
                diff_data[subsection] = []

        sections['differentiation_subsections'] = diff_data

        return sections

    def update_from_parsed_content(self):
        """Update model fields from parsed content"""
        parsed = self.parse_generated_content()

        # Update metadata fields if they exist in parsed content
        metadata = parsed.get('metadata_fields', {})
        if metadata:
            self.subject = metadata.get('subject', self.subject)
            self.grade_level = metadata.get('grade_level', self.grade_level)
            self.quarter = metadata.get('quarter', self.quarter)

            # Extract duration value (remove "minutes" if present)
            duration_str = metadata.get('duration', '')
            if duration_str:
                try:
                    self.duration = int(''.join(filter(str.isdigit, duration_str)))
                except (ValueError, TypeError):
                    pass

            # Extract population value
            population_str = metadata.get('class_size', '')
            if population_str:
                try:
                    self.population = int(''.join(filter(str.isdigit, population_str)))
                except (ValueError, TypeError):
                    pass

        # Update procedure subsections if they exist
        procedure_subsections = parsed.get('procedure_subsections', {})
        if procedure_subsections:
            # Map these to your existing fields or create new ones if needed
            pass

        return parsed

    # Add this method to your LessonPlan model in lessonGenerator app
    def submit_for_approval(self, department_head):
        """Submit this lesson plan to a department head for approval"""
        from lesson.models import LessonPlanSubmission  # Import here to avoid circular import
        
        # Validate that teacher and department head are in same school and department
        if self.created_by.school != department_head.school:
            return False, f"Department Head {department_head.full_name} is not in your school ({self.created_by.school})."
        
        if self.created_by.department != department_head.department:
            return False, f"Department Head {department_head.full_name} is not in your department ({self.created_by.department})."
        
        # Check if already submitted
        existing_submission = LessonPlanSubmission.objects.filter(
            lesson_plan=self, 
            status__in=['submitted', 'approved', 'needs_revision']
        ).first()
        
        if existing_submission:
            return False, "This lesson plan has already been submitted for approval."
        
        # Create new submission
        try:
            submission = LessonPlanSubmission.objects.create(
                lesson_plan=self,
                submitted_by=self.created_by,
                submitted_to=department_head,
                status='submitted'
            )
            return True, f"Lesson plan submitted successfully to {department_head.full_name}!"
        except ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Error submitting lesson plan: {str(e)}"

    def get_structured_content(self):
        """Return lesson plan content in a structured format for templates"""
        parsed = self.parse_generated_content()
        
        # If we have parsed content from AI, use it
        if parsed and parsed.get('metadata_fields'):
            return {
                'metadata': parsed.get('metadata_fields', {}),
                'learning_objectives': parsed.get('learning_objectives_list', []),
                'subject_matter': parsed.get('subject_matter', ''),
                'materials': parsed.get('materials_list', []),
                'procedure': parsed.get('procedure_subsections', {}),
                'differentiation': parsed.get('differentiation_subsections', {})
            }
        
        # Fallback to model fields
        return {
            'metadata': {
                'subject': self.subject,
                'grade_level': self.grade_level,
                'quarter': self.quarter,
                'duration': self.duration,
                'class_size': self.population
            },
            'learning_objectives': self.learning_objectives.split('\n') if self.learning_objectives else [],
            'subject_matter': self.subject_matter,
            'materials': self.materials_needed.split('\n') if self.materials_needed else [],
            'procedure': {
                'introduction': {'content': self.introduction},
                'instruction': {'content': self.instruction},
                'application': {'content': self.application},
                'evaluation': {'content': self.evaluation},
                'assessment': {'content': self.assessment}
            }
        }