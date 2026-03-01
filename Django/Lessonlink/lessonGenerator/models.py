# models.py
import re
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class LessonPlan(models.Model):
    DRAFT = 'draft'
    FINAL = 'final'
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (FINAL, 'Final'),
    ]

    
    INTELLIGENCE_TYPE_CHOICES = [
        ('comprehensive', 'Comprehensive (IQ+EQ+SQ+AQ)'),
        ('cognitive', 'Cognitive Focus (IQ) - Logical & Analytical'),
        ('emotional', 'Emotional Focus (EQ) - Self & Social Awareness'),
        ('social', 'Social Focus (SQ) - Collaboration & Communication'),
        ('resilience', 'Resilience Focus (AQ) - Perseverance & Adaptability'),
        ('differentiated', 'Differentiated Mix - All Types with Varied Activities'),
    ]

    # Basic Information
    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=100)
    grade_level = models.CharField(max_length=50)
    quarter = models.CharField(max_length=50, blank=True)
    duration = models.IntegerField(help_text="Duration in minutes")
    population = models.IntegerField(help_text="Number of students")
    
    # Lesson Content
    learning_objectives = models.TextField()
    subject_matter = models.TextField()
    materials_needed = models.TextField()
    
    # Procedure Sections
    introduction = models.TextField()
    instruction = models.TextField()
    application = models.TextField()
    evaluation = models.TextField()
    assessment = models.TextField()
    
    # MELC Alignment Fields
    melc_code = models.CharField(max_length=50, blank=True)
    content_standard = models.TextField(blank=True)
    performance_standard = models.TextField(blank=True)
    learning_competency = models.TextField(blank=True)
    
    # Integration Fields
    values_integration = models.TextField(blank=True)
    cross_curricular = models.TextField(blank=True)
    
    # System Fields
    generated_content = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT)
    auto_approved = models.BooleanField(default=False, help_text="Automatically approved for department heads")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    intelligence_type = models.CharField(
        max_length=20,
        choices=INTELLIGENCE_TYPE_CHOICES,
        default='comprehensive',
        help_text="Type of intelligence to focus lesson plan adaptation on"
    )

    def __str__(self):
        return f"{self.subject} - {self.grade_level} - {self.title}"

    def parse_generated_content(self):
        """Parse the AI-generated content into sections and subsections including MELC and exemplar data"""
        sections = {}
        content = self.generated_content

        # Define patterns for each main section
        patterns = {
            'metadata': r'## Metadata\s*\n(.*?)(?=##|$)',
            'melc_alignment': r'## MELC Alignment\s*\n(.*?)(?=##|$)',
            'learning_objectives': r'## Learning Objectives\s*\n(.*?)(?=##|$)',
            'subject_matter': r'## Subject Matter\s*\n(.*?)(?=##|$)',
            'materials_needed': r'## Materials Needed\s*\n(.*?)(?=##|$)',
            'lesson_procedure': r'## Lesson Procedure\s*\n(.*?)(?=##|$)',
            'differentiation': r'## Differentiation\s*\n(.*?)(?=##|$)',
            'integration': r'## Integration\s*\n(.*?)(?=##|$)',
            'exemplar_notes': r'## Exemplar Notes\s*\n(.*?)(?=##|$)',  # Add exemplar notes
        }

        for section, pattern in patterns.items():
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                sections[section] = match.group(1).strip()
            else:
                sections[section] = ""

        # Parse Metadata fields - ADD EXEMPLAR REFERENCE
        metadata = sections.get('metadata', '')
        metadata_patterns = {
            'subject': r'\*\*Subject:\*\*\s*([^\n]+)',
            'grade_level': r'\*\*Grade Level:\*\*\s*([^\n]+)',
            'quarter': r'\*\*Quarter:\*\*\s*([^\n]+)',
            'duration': r'\*\*Duration:\*\*\s*([^\n]+)',
            'class_size': r'\*\*Class Size:\*\*\s*([^\n]+)',
            'exemplar_referenced': r'\*\*Exemplar Referenced:\*\*\s*([^\n]+)',  # Add exemplar reference
        }

        metadata_data = {}
        for field, pattern in metadata_patterns.items():
            match = re.search(pattern, metadata, re.IGNORECASE)
            if match:
                metadata_data[field] = match.group(1).strip()
            else:
                metadata_data[field] = ""

        sections['metadata_fields'] = metadata_data

        # Parse MELC Alignment fields
        melc_alignment = sections.get('melc_alignment', '')
        melc_patterns = {
            'melc_code': r'\*\*MELC Code:\*\*\s*([^\n]+)',
            'content_standard': r'\*\*Content Standard:\*\*\s*([^\n]+)',
            'performance_standard': r'\*\*Performance Standard:\*\*\s*([^\n]+)',
            'learning_competency': r'\*\*Learning Competency:\*\*\s*([^\n]+)',
        }

        melc_data = {}
        for field, pattern in melc_patterns.items():
            match = re.search(pattern, melc_alignment, re.IGNORECASE)
            if match:
                melc_data[field] = match.group(1).strip()
            else:
                melc_data[field] = ""

        sections['melc_fields'] = melc_data

        # Parse Integration fields
        integration = sections.get('integration', '')
        integration_patterns = {
            'values_education': r'\*\*Values Education:\*\*\s*([^\n]+)',
            'cross_curricular': r'\*\*Cross-curricular:\*\*\s*([^\n]+)',
        }

        integration_data = {}
        for field, pattern in integration_patterns.items():
            match = re.search(pattern, integration, re.IGNORECASE)
            if match:
                integration_data[field] = match.group(1).strip()
            else:
                integration_data[field] = ""

        sections['integration_fields'] = integration_data

        # Parse Exemplar Notes fields
        exemplar_notes = sections.get('exemplar_notes', '')
        exemplar_patterns = {
            'used_as_reference': r'\*\*Used as Reference:\*\*\s*([^\n]+)',
            'structural_influence': r'\*\*Structural Influence:\*\*\s*([^\n]+)',
            'quality_standards': r'\*\*Quality Standards:\*\*\s*([^\n]+)',
        }

        exemplar_data = {}
        for field, pattern in exemplar_patterns.items():
            match = re.search(pattern, exemplar_notes, re.IGNORECASE)
            if match:
                exemplar_data[field] = match.group(1).strip()
            else:
                exemplar_data[field] = ""

        sections['exemplar_fields'] = exemplar_data

        # Parse Learning Objectives as list items
        objectives = sections.get('learning_objectives', '')
        objectives_list = re.findall(r'\*\s*(.*?)(?=\n\*|\n\n|$)', objectives, re.DOTALL)
        sections['learning_objectives_list'] = [obj.strip() for obj in objectives_list if obj.strip()]

        # Parse Materials Needed as list items
        materials = sections.get('materials_needed', '')
        materials_list = re.findall(r'\*\s*(.*?)(?=\n\*|\n\n|$)', materials, re.DOTALL)
        sections['materials_list'] = [mat.strip() for mat in materials_list if mat.strip()]

        # Parse Lesson Procedure subsections - ADD EXEMPLAR INFLUENCE
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
                content = match.group(2).strip()
                # Extract exemplar influence if present
                exemplar_influence_match = re.search(r'\*\*Exemplar Influence:\*\*\s*(.*?)(?=\n\n|\n\*|\n###|$)', content, re.DOTALL | re.IGNORECASE)
                exemplar_influence = exemplar_influence_match.group(1).strip() if exemplar_influence_match else ""
                
                procedure_data[subsection] = {
                    'time': match.group(1).strip(),
                    'content': content,
                    'exemplar_influence': exemplar_influence
                }
            else:
                procedure_data[subsection] = {'time': '', 'content': '', 'exemplar_influence': ''}

        sections['procedure_subsections'] = procedure_data

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
        """Update model fields from parsed content including MELC data"""
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

        # Update MELC fields
        melc_fields = parsed.get('melc_fields', {})
        if melc_fields:
            self.melc_code = melc_fields.get('melc_code', self.melc_code)
            self.content_standard = melc_fields.get('content_standard', self.content_standard)
            self.performance_standard = melc_fields.get('performance_standard', self.performance_standard)
            self.learning_competency = melc_fields.get('learning_competency', self.learning_competency)

        # Update Integration fields
        integration_fields = parsed.get('integration_fields', {})
        if integration_fields:
            self.values_integration = integration_fields.get('values_education', self.values_integration)
            self.cross_curricular = integration_fields.get('cross_curricular', self.cross_curricular)

        return parsed

    def submit_for_approval(self, department_head):
        """Submit this lesson plan to a department head for approval"""
        # Import here to avoid circular import
        from .models import LessonPlanSubmission
        
        # Validate that teacher and department head are in same school and department
        if hasattr(self.created_by, 'school') and hasattr(department_head, 'school'):
            if self.created_by.school != department_head.school:
                return False, f"Department Head {getattr(department_head, 'full_name', department_head.username)} is not in your school ({self.created_by.school})."
        
        if hasattr(self.created_by, 'department') and hasattr(department_head, 'department'):
            if self.created_by.department != department_head.department:
                return False, f"Department Head {getattr(department_head, 'full_name', department_head.username)} is not in your department ({self.created_by.department})."
        
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
            return True, f"Lesson plan submitted successfully to {getattr(department_head, 'full_name', department_head.username)}!"
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
                'melc_alignment': parsed.get('melc_fields', {}),
                'learning_objectives': parsed.get('learning_objectives_list', []),
                'subject_matter': parsed.get('subject_matter', ''),
                'materials': parsed.get('materials_list', []),
                'procedure': parsed.get('procedure_subsections', {}),
                'differentiation': parsed.get('differentiation_subsections', {}),
                'integration': parsed.get('integration_fields', {})
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
            'melc_alignment': {
                'melc_code': self.melc_code,
                'content_standard': self.content_standard,
                'performance_standard': self.performance_standard,
                'learning_competency': self.learning_competency
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
            },
            'integration': {
                'values_education': self.values_integration,
                'cross_curricular': self.cross_curricular
            }
        }
    
    def get_latest_submission(self):
        """Get the latest submission for this lesson plan"""
        try:
            return LessonPlanSubmission.objects.filter(
                lesson_plan=self
            ).order_by('-submission_date').first()
        except LessonPlanSubmission.DoesNotExist:
            return None

    @property
    def latest_submission(self):
        return self.get_latest_submission()


class LessonPlanSubmission(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('needs_revision', 'Needs Revision'),
        ('rejected', 'Rejected'),
    ]
    
    lesson_plan = models.ForeignKey(LessonPlan, on_delete=models.CASCADE, related_name='submissions')
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submitted_plans')
    submitted_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_submissions')
    submission_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    feedback = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-submission_date']
    
    def __str__(self):
        return f"{self.lesson_plan.title} - {self.status}"

    def submit_to_supervising_teacher(self):
        """Submit lesson plan to supervising teacher for review - specifically for Student Teachers"""
        if not self.created_by.supervising_teacher:
            return False, "No supervising teacher assigned"
        
        if self.status != self.DRAFT:
            return False, "Only draft lesson plans can be submitted"
        
        # Check if already submitted to this supervising teacher
        existing_submission = LessonPlanSubmission.objects.filter(
            lesson_plan=self,
            submitted_to=self.created_by.supervising_teacher,
            status__in=['submitted', 'approved', 'needs_revision']
        ).first()
        
        if existing_submission:
            status_display = existing_submission.get_status_display()
            return False, f"Already submitted to supervising teacher. Current status: {status_display}"
        
        # Validate school and department match
        if (self.created_by.school != self.created_by.supervising_teacher.school or 
            self.created_by.department != self.created_by.supervising_teacher.department):
            return False, "Supervising teacher is not in your school/department"
        
        try:
            # Create submission record
            submission = LessonPlanSubmission.objects.create(
                lesson_plan=self,
                submitted_by=self.created_by,
                submitted_to=self.created_by.supervising_teacher,
                status='submitted'
            )
            
            return True, f"Lesson plan submitted to {self.created_by.supervising_teacher.full_name} successfully!"
            
        except ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Error submitting lesson plan: {str(e)}"
        
        @classmethod
        def get_active_submission_for_lesson(cls, lesson_plan, submitted_to):
            """Get active submission for a lesson plan to a specific recipient"""
            return cls.objects.filter(
                lesson_plan=lesson_plan,
                submitted_to=submitted_to,
                status__in=['submitted', 'approved', 'needs_revision']
            ).first()

# Add to your existing models.py

class WeeklyLessonPlan(models.Model):
    """
    Weekly Lesson Plan model following DepEd MATATAG Curriculum standards
    Supports 5-day weekly lesson planning with daily breakdowns
    """
    DRAFT = 'draft'
    FINAL = 'final'
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (FINAL, 'Final'),
    ]

    INTELLIGENCE_TYPE_CHOICES = [
        ('comprehensive', 'Comprehensive (IQ+EQ+SQ+AQ)'),
        ('cognitive', 'Cognitive Focus (IQ) - Logical & Analytical'),
        ('emotional', 'Emotional Focus (EQ) - Self & Social Awareness'),
        ('social', 'Social Focus (SQ) - Collaboration & Communication'),
        ('resilience', 'Resilience Focus (AQ) - Perseverance & Adaptability'),
        ('differentiated', 'Differentiated Mix - All Types with Varied Activities'),
    ]

    WEEK_DAYS = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
    ]

    # Basic Information
    title = models.CharField(max_length=200, help_text="Weekly lesson title")
    subject = models.CharField(max_length=100)
    grade_level = models.CharField(max_length=50)
    quarter = models.CharField(max_length=50)
    week_number = models.IntegerField(help_text="Week number in the quarter (1-10)")
    
    # School Information
    school = models.CharField(max_length=200, blank=True)
    teacher = models.CharField(max_length=200, blank=True)
    teaching_date = models.CharField(max_length=100, blank=True, help_text="Teaching date range")
    
    # Weekly Standards
    content_standard = models.TextField(help_text="MATATAG Content Standards for the week")
    performance_standard = models.TextField(help_text="MATATAG Performance Standards for the week")
    
    # Learning Objectives - One per day
    objective_monday = models.TextField(blank=True)
    objective_tuesday = models.TextField(blank=True)
    objective_wednesday = models.TextField(blank=True)
    objective_thursday = models.TextField(blank=True)
    objective_friday = models.TextField(blank=True)
    
    # Daily Content/Topics
    content_monday = models.TextField(blank=True)
    content_tuesday = models.TextField(blank=True)
    content_wednesday = models.TextField(blank=True)
    content_thursday = models.TextField(blank=True)
    content_friday = models.TextField(blank=True)
    
    # Learning Resources
    teachers_guide = models.CharField(max_length=200, blank=True)
    learning_materials = models.CharField(max_length=200, blank=True)
    textbook_pages = models.CharField(max_length=200, blank=True)
    lr_portal = models.CharField(max_length=200, blank=True, help_text="Learning Resource Portal references")
    other_resources = models.TextField(blank=True)
    
    # Daily Procedures (MATATAG 5-step procedure per day)
    # Monday
    monday_procedure_a = models.TextField(blank=True, help_text="A. Reviewing previous lesson")
    monday_procedure_b = models.TextField(blank=True, help_text="B. Establishing purpose")
    monday_procedure_c = models.TextField(blank=True, help_text="C. Presenting examples")
    monday_procedure_d = models.TextField(blank=True, help_text="D. Discussing concepts #1")
    monday_procedure_e = models.TextField(blank=True, help_text="E. Discussing concepts #2")
    monday_procedure_f = models.TextField(blank=True, help_text="F. Developing mastery")
    monday_procedure_g = models.TextField(blank=True, help_text="G. Finding practical applications")
    monday_procedure_h = models.TextField(blank=True, help_text="H. Making generalizations")
    monday_procedure_i = models.TextField(blank=True, help_text="I. Evaluating learning")
    monday_procedure_j = models.TextField(blank=True, help_text="J. Additional activities")
    
    # Tuesday
    tuesday_procedure_a = models.TextField(blank=True)
    tuesday_procedure_b = models.TextField(blank=True)
    tuesday_procedure_c = models.TextField(blank=True)
    tuesday_procedure_d = models.TextField(blank=True)
    tuesday_procedure_e = models.TextField(blank=True)
    tuesday_procedure_f = models.TextField(blank=True)
    tuesday_procedure_g = models.TextField(blank=True)
    tuesday_procedure_h = models.TextField(blank=True)
    tuesday_procedure_i = models.TextField(blank=True)
    tuesday_procedure_j = models.TextField(blank=True)
    
    # Wednesday
    wednesday_procedure_a = models.TextField(blank=True)
    wednesday_procedure_b = models.TextField(blank=True)
    wednesday_procedure_c = models.TextField(blank=True)
    wednesday_procedure_d = models.TextField(blank=True)
    wednesday_procedure_e = models.TextField(blank=True)
    wednesday_procedure_f = models.TextField(blank=True)
    wednesday_procedure_g = models.TextField(blank=True)
    wednesday_procedure_h = models.TextField(blank=True)
    wednesday_procedure_i = models.TextField(blank=True)
    wednesday_procedure_j = models.TextField(blank=True)
    
    # Thursday
    thursday_procedure_a = models.TextField(blank=True)
    thursday_procedure_b = models.TextField(blank=True)
    thursday_procedure_c = models.TextField(blank=True)
    thursday_procedure_d = models.TextField(blank=True)
    thursday_procedure_e = models.TextField(blank=True)
    thursday_procedure_f = models.TextField(blank=True)
    thursday_procedure_g = models.TextField(blank=True)
    thursday_procedure_h = models.TextField(blank=True)
    thursday_procedure_i = models.TextField(blank=True)
    thursday_procedure_j = models.TextField(blank=True)
    
    # Friday
    friday_procedure_a = models.TextField(blank=True)
    friday_procedure_b = models.TextField(blank=True)
    friday_procedure_c = models.TextField(blank=True)
    friday_procedure_d = models.TextField(blank=True)
    friday_procedure_e = models.TextField(blank=True)
    friday_procedure_f = models.TextField(blank=True)
    friday_procedure_g = models.TextField(blank=True)
    friday_procedure_h = models.TextField(blank=True)
    friday_procedure_i = models.TextField(blank=True)
    friday_procedure_j = models.TextField(blank=True)
    
    # Weekly Theme and Approach
    weekly_theme = models.CharField(max_length=50, blank=True, choices=[
        ('introduction', 'Introduction'),
        ('skill_building', 'Skill Building'),
        ('deep_dive', 'Deep Dive'),
        ('practice', 'Practice'),
        ('assessment', 'Assessment'),
    ])
    teaching_approach = models.CharField(max_length=50, blank=True, choices=[
        ('direct', 'Direct Instruction'),
        ('collaborative', 'Collaborative Learning'),
        ('hands_on', 'Hands-on/Practical'),
        ('inquiry', 'Inquiry-Based'),
    ])
    
    # Intelligence Type
    intelligence_type = models.CharField(
        max_length=20,
        choices=INTELLIGENCE_TYPE_CHOICES,
        default='comprehensive',
        help_text="Type of intelligence to focus lesson plan adaptation on"
    )
    
    # Exemplar Reference
    exemplar_used = models.ForeignKey('lesson.Exemplar', on_delete=models.SET_NULL, null=True, blank=True)
    exemplar_notes = models.TextField(blank=True, help_text="How exemplar influenced this weekly plan")
    
    # MELC Alignment
    melc_codes = models.TextField(blank=True, help_text="MELC codes covered this week (comma separated)")
    
    # Integration
    values_integration = models.TextField(blank=True)
    cross_curricular = models.TextField(blank=True)
    
    # Full Generated Content (for reference)
    generated_content = models.TextField(help_text="Full AI-generated weekly lesson plan in markdown")
    
    # System Fields
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT)
    auto_approved = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='weekly_plans')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Submission tracking (reuse LessonPlanSubmission with type field)
    is_weekly = models.BooleanField(default=True, help_text="Indicator for weekly lesson plans")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Weekly Lesson Plan'
        verbose_name_plural = 'Weekly Lesson Plans'
    
    def __str__(self):
        return f"Week {self.week_number}: {self.subject} - {self.grade_level} ({self.get_status_display()})"
    
    def get_objectives_dict(self):
        """Return objectives as a dictionary by day"""
        return {
            'monday': self.objective_monday,
            'tuesday': self.objective_tuesday,
            'wednesday': self.objective_wednesday,
            'thursday': self.objective_thursday,
            'friday': self.objective_friday,
        }
    
    def get_content_dict(self):
        """Return content/topics as a dictionary by day"""
        return {
            'monday': self.content_monday,
            'tuesday': self.content_tuesday,
            'wednesday': self.content_wednesday,
            'thursday': self.content_thursday,
            'friday': self.content_friday,
        }
    
    def get_procedure_for_day(self, day):
        """Get all procedure steps for a specific day"""
        steps = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
        procedure = {}
        
        for step in steps:
            field_name = f"{day}_procedure_{step}"
            if hasattr(self, field_name):
                procedure[step] = getattr(self, field_name)
            else:
                procedure[step] = ""
        
        return procedure
    
    def get_latest_submission(self):
        """Get the latest submission for this weekly plan"""
        try:
            from .models import LessonPlanSubmission
            return LessonPlanSubmission.objects.filter(
                lesson_plan_id=self.id,
                is_weekly=True
            ).order_by('-submission_date').first()
        except:
            return None
    
    @property
    def latest_submission(self):
        return self.get_latest_submission()
    
    def submit_for_approval(self, department_head):
        """Submit this weekly plan for approval"""
        from .models import LessonPlanSubmission
        
        # Check if already submitted
        existing_submission = LessonPlanSubmission.objects.filter(
            lesson_plan_id=self.id,
            is_weekly=True,
            status__in=['submitted', 'approved', 'needs_revision']
        ).first()
        
        if existing_submission:
            return False, "This weekly plan has already been submitted for approval."
        
        try:
            submission = LessonPlanSubmission.objects.create(
                lesson_plan_id=self.id,
                is_weekly=True,
                submitted_by=self.created_by,
                submitted_to=department_head,
                status='submitted'
            )
            return True, f"Weekly plan submitted successfully to {department_head.full_name}!"
        except Exception as e:
            return False, f"Error submitting: {str(e)}"
    
      # Add submission status field (can be separate from DRAFT/FINAL)
    submission_status = models.CharField(
        max_length=20,
        choices=[
            ('not_submitted', 'Not Submitted'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('needs_revision', 'Needs Revision'),
        ],
        default='not_submitted'
    )
    
    # Add fields for submission tracking
    submitted_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='weekly_plans_received'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='weekly_plans_reviewed'
    )
    review_notes = models.TextField(blank=True)
    
    # ... rest of existing fields ...
    
    def submit_for_approval(self, reviewer):
        """Submit this weekly plan for approval"""
        self.submission_status = 'submitted'
        self.submitted_to = reviewer
        self.submitted_at = timezone.now()
        self.status = self.FINAL  # Change status to FINAL when submitted
        self.save()
        
        # Create notification for reviewer
        try:
            from lessonlinkNotif.models import Notification
            Notification.objects.create(
                user=reviewer,
                title=f"Weekly Plan Submitted: {self.title}",
                message=f"{self.created_by.get_full_name()} submitted a weekly lesson plan for review.",
                notification_type='lesson_submitted',
                related_id=self.id,
                related_type='weekly_lesson_plan'
            )
        except:
            pass
        
        return True, f"Weekly plan submitted successfully to {reviewer.get_full_name()}!"
    
    def approve(self, reviewer, notes=""):
        """Approve this weekly plan"""
        self.submission_status = 'approved'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.status = self.FINAL
        self.save()
        
        # Create notification for creator
        try:
            from lessonlinkNotif.models import Notification
            Notification.objects.create(
                user=self.created_by,
                title=f"Weekly Plan Approved: {self.title}",
                message=f"Your weekly lesson plan has been approved by {reviewer.get_full_name()}.",
                notification_type='draft_approved',
                related_id=self.id,
                related_type='weekly_lesson_plan'
            )
        except:
            pass
        
        return True, "Weekly plan approved successfully!"
    
    def reject(self, reviewer, notes):
        """Reject this weekly plan"""
        self.submission_status = 'rejected'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.status = self.DRAFT  # Revert to draft
        self.save()
        
        # Create notification for creator
        try:
            from lessonlinkNotif.models import Notification
            Notification.objects.create(
                user=self.created_by,
                title=f"Weekly Plan Needs Revision: {self.title}",
                message=f"Your weekly lesson plan needs revision. Feedback: {notes[:100]}...",
                notification_type='draft_rejected',
                related_id=self.id,
                related_type='weekly_lesson_plan'
            )
        except:
            pass
        
        return True, "Weekly plan rejected with feedback."
    
    def needs_revision(self, reviewer, notes):
        """Request revision for this weekly plan"""
        self.submission_status = 'needs_revision'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.status = self.DRAFT
        self.save()
        
        # Create notification for creator
        try:
            from lessonlinkNotif.models import Notification
            Notification.objects.create(
                user=self.created_by,
                title=f"Weekly Plan Needs Revision: {self.title}",
                message=f"Your weekly lesson plan needs revision. Feedback: {notes[:100]}...",
                notification_type='draft_rejected',
                related_id=self.id,
                related_type='weekly_lesson_plan'
            )
        except:
            pass
        
        return True, "Weekly plan marked for revision with feedback."

    @property
    def get_submission_status_display_custom(self):
        """Get human-readable submission status"""
        status_map = {
            'not_submitted': 'Not Submitted',
            'submitted': 'Submitted',
            'approved': 'Approved',
            'rejected': 'Rejected',
            'needs_revision': 'Needs Revision',
        }
        return status_map.get(self.submission_status, self.submission_status)
    
    @property
    def can_submit(self):
        """Check if this weekly plan can be submitted"""
        return self.submission_status in ['not_submitted', 'rejected', 'needs_revision']


# Add is_weekly field to LessonPlanSubmission
# Add this field to your existing LessonPlanSubmission model
"""
is_weekly = models.BooleanField(default=False, help_text="Whether this submission is for a weekly lesson plan")
"""


class WeeklyLessonPlanSubmission(models.Model):
    """
    Submission tracking specifically for weekly lesson plans
    (Alternative approach - use this if you prefer separate model)
    """
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('needs_revision', 'Needs Revision'),
        ('rejected', 'Rejected'),
    ]
    
    weekly_plan = models.ForeignKey(WeeklyLessonPlan, on_delete=models.CASCADE, related_name='submissions')
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='weekly_submissions')
    submitted_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_weekly_submissions')
    submission_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    feedback = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-submission_date']
    
    def __str__(self):
        return f"Week {self.weekly_plan.week_number}: {self.status}"