import json
import google.generativeai as genai
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import LessonPlan
from django.contrib import messages
import re


from .ai_instructions import LESSON_PLANNER_SYSTEM_INSTRUCTION

# Configure the Gemini API
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"Gemini configuration error: {e}")
    model = None

def lesson_ai(request):
    """Render the main page with the lesson plan form"""
    return render(request, 'lessonGenerator/lesson_ai.html')

@csrf_exempt
@require_http_methods(["POST"])
def generate_lesson_plan(request):
    try:
        # Check if Gemini is configured properly
        if model is None:
            return JsonResponse({
                'success': False,
                'error': 'AI service is not configured properly. Please check your API key.'
            }, status=500)
            
        # Parse JSON data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data received.'
            }, status=400)
        
        # Extract form data with validation
        required_fields = ['subject', 'grade_level', 'learning_objectives']
        for field in required_fields:
            if field not in data or not data[field].strip():
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        form_data = {
            'subject': data.get('subject', '').strip(),
            'grade_level': data.get('grade_level', '').strip(),
            'quarter': data.get('quarter', '').strip(),
            'duration': data.get('duration', '').strip(),
            'population': data.get('population', '').strip(),
            'learning_objectives': data.get('learning_objectives', '').strip(),
            'subject_matter': data.get('subject_matter', '').strip(),
            'materials_needed': data.get('materials_needed', '').strip(),
            'introduction': data.get('introduction', '').strip(),
            'instruction': data.get('instruction', '').strip(),
            'application': data.get('application', '').strip(),
            'evaluation': data.get('evaluation', '').strip(),
            'assessment': data.get('assessment', '').strip(),
        }
        
        # Format the prompt for the AI
        prompt = f"""
        Create a comprehensive lesson plan based on these details:

        SUBJECT: {form_data['subject']}
        GRADE LEVEL: {form_data['grade_level']}
        QUARTER: {form_data['quarter']}
        DURATION: {form_data['duration']} minutes
        CLASS SIZE: {form_data['population']} students
        LEARNING OBJECTIVES: {form_data['learning_objectives']}
        SUBJECT MATTER: {form_data['subject_matter']}
        MATERIALS NEEDED: {form_data['materials_needed']}
        INTRODUCTION: {form_data['introduction']}
        INSTRUCTION: {form_data['instruction']}
        APPLICATION: {form_data['application']}
        EVALUATION: {form_data['evaluation']}
        ASSESSMENT: {form_data['assessment']}

        Please generate a complete lesson plan using the specified format.
        """
        
        # Generate the lesson plan using Gemini
        try:
            response = model.generate_content([
                LESSON_PLANNER_SYSTEM_INSTRUCTION,
                prompt
            ])
            
            # Parse the generated content into sections
            parsed_content = parse_lesson_plan_content(response.text)
            
            # Store the parsed content and original text in session
            request.session['generated_lesson_plan'] = response.text
            request.session['parsed_lesson_plan'] = parsed_content
            request.session['lesson_form_data'] = form_data
            request.session.modified = True
            
            return JsonResponse({
                'success': True,
                'lesson_plan': response.text
            })
            
        except Exception as ai_error:
            return JsonResponse({
                'success': False,
                'error': f'AI service error: {str(ai_error)}'
            }, status=500)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)

def parse_lesson_plan_content(content):
    """Parse the AI-generated lesson plan content into structured data"""
    parsed_data = {
        'metadata': {},
        'learning_objectives': [],
        'subject_matter': {},
        'materials_needed': [],
        'procedure': {},
        'differentiation': {}
    }
    
    # Parse metadata
    metadata_match = re.search(r'## Metadata\s*\n(.*?)(?=##|$)', content, re.DOTALL | re.IGNORECASE)
    if metadata_match:
        metadata_text = metadata_match.group(1)
        metadata_patterns = {
            'subject': r'\*\*Subject:\*\*\s*([^\n]+)',
            'grade_level': r'\*\*Grade Level:\*\*\s*([^\n]+)',
            'quarter': r'\*\*Quarter:\*\*\s*([^\n]+)',
            'duration': r'\*\*Duration:\*\*\s*([^\n]+)',
            'class_size': r'\*\*Class Size:\*\*\s*([^\n]+)',
        }
        
        for field, pattern in metadata_patterns.items():
            match = re.search(pattern, metadata_text, re.IGNORECASE)
            if match:
                parsed_data['metadata'][field] = match.group(1).strip()
    
    # Parse learning objectives
    objectives_match = re.search(r'## Learning Objectives\s*\n(.*?)(?=##|$)', content, re.DOTALL | re.IGNORECASE)
    if objectives_match:
        objectives_text = objectives_match.group(1)
        objectives_list = re.findall(r'\*\s*(.*?)(?=\n\*|\n\n|$)', objectives_text, re.DOTALL)
        parsed_data['learning_objectives'] = [obj.strip() for obj in objectives_list if obj.strip()]
    
    # Parse subject matter
    subject_matter_match = re.search(r'## Subject Matter\s*\n(.*?)(?=##|$)', content, re.DOTALL | re.IGNORECASE)
    if subject_matter_match:
        subject_matter_text = subject_matter_match.group(1)
        # Extract topic
        topic_match = re.search(r'\*\*Topic:\*\*\s*([^\n]+)', subject_matter_text, re.IGNORECASE)
        if topic_match:
            parsed_data['subject_matter']['topic'] = topic_match.group(1).strip()
        
        # Extract key concepts
        concepts_match = re.search(r'\*\*Key Concepts:\*\*\s*([^\n]+)', subject_matter_text, re.IGNORECASE)
        if concepts_match:
            parsed_data['subject_matter']['key_concepts'] = concepts_match.group(1).strip()
        
        # Extract vocabulary
        vocab_match = re.search(r'\*\*Vocabulary:\*\*\s*([^\n]+)', subject_matter_text, re.IGNORECASE)
        if vocab_match:
            parsed_data['subject_matter']['vocabulary'] = vocab_match.group(1).strip()
    
    # Parse materials needed
    materials_match = re.search(r'## Materials Needed\s*\n(.*?)(?=##|$)', content, re.DOTALL | re.IGNORECASE)
    if materials_match:
        materials_text = materials_match.group(1)
        materials_list = re.findall(r'\*\s*(.*?)(?=\n\*|\n\n|$)', materials_text, re.DOTALL)
        parsed_data['materials_needed'] = [mat.strip() for mat in materials_list if mat.strip()]
    
    # Parse lesson procedure
    procedure_match = re.search(r'## Lesson Procedure\s*\n(.*?)(?=##|$)', content, re.DOTALL | re.IGNORECASE)
    if procedure_match:
        procedure_text = procedure_match.group(1)
        
        # Parse each subsection
        subsection_patterns = {
            'introduction': r'### A\. Introduction\s*\(([^)]+)\)\s*\n(.*?)(?=###|$)',
            'instruction': r'### B\. Instruction/Direct Teaching\s*\(([^)]+)\)\s*\n(.*?)(?=###|$)',
            'application': r'### C\. Guided Practice/Application\s*\(([^)]+)\)\s*\n(.*?)(?=###|$)',
            'evaluation': r'### D\. Independent Practice/Evaluation\s*\(([^)]+)\)\s*\n(.*?)(?=###|$)',
            'assessment': r'### E\. Assessment\s*\(([^)]+)\)\s*\n(.*?)(?=###|$)',
        }
        
        for section, pattern in subsection_patterns.items():
            match = re.search(pattern, procedure_text, re.DOTALL | re.IGNORECASE)
            if match:
                parsed_data['procedure'][section] = {
                    'time': match.group(1).strip(),
                    'content': match.group(2).strip()
                }
    
    # Parse differentiation
    differentiation_match = re.search(r'## Differentiation\s*\n(.*?)(?=##|$)', content, re.DOTALL | re.IGNORECASE)
    if differentiation_match:
        differentiation_text = differentiation_match.group(1)
        
        # Parse support for struggling learners
        support_match = re.search(r'\*\*Support for Struggling Learners:\*\*\s*(.*?)(?=\*\*|$)', differentiation_text, re.DOTALL | re.IGNORECASE)
        if support_match:
            support_items = re.findall(r'\*\s*(.*?)(?=\n\*|\n\n|$)', support_match.group(1), re.DOTALL)
            parsed_data['differentiation']['support'] = [item.strip() for item in support_items if item.strip()]
        
        # Parse extension for advanced learners
        extension_match = re.search(r'\*\*Extension for Advanced Learners:\*\*\s*(.*?)(?=\*\*|$)', differentiation_text, re.DOTALL | re.IGNORECASE)
        if extension_match:
            extension_items = re.findall(r'\*\s*(.*?)(?=\n\*|\n\n|$)', extension_match.group(1), re.DOTALL)
            parsed_data['differentiation']['extension'] = [item.strip() for item in extension_items if item.strip()]
    
    return parsed_data

def lesson_plan_result(request):
    """Render the lesson plan result page"""
    lesson_plan = request.session.get('generated_lesson_plan', '')
    return render(request, 'lessonGenerator/lesson_plan.html', {
        'lesson_plan': lesson_plan
    })

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def save_lesson_plan(request):
    """Save the generated lesson plan as a draft with parsed sections"""
    try:
        # Get data from session
        generated_content = request.session.get('generated_lesson_plan', '')
        parsed_content = request.session.get('parsed_lesson_plan', {})
        form_data = request.session.get('lesson_form_data', {})
        
        if not generated_content:
            return JsonResponse({
                'success': False,
                'error': 'No lesson plan content found. Please generate a lesson plan first.'
            }, status=400)
        
        # Create a new LessonPlan instance using the parsed content
        lesson_plan = LessonPlan(
            title=f"{parsed_content.get('metadata', {}).get('subject', 'Untitled')} - {parsed_content.get('metadata', {}).get('grade_level', '')}",
            subject=parsed_content.get('metadata', {}).get('subject', form_data.get('subject', '')),
            grade_level=parsed_content.get('metadata', {}).get('grade_level', form_data.get('grade_level', '')),
            quarter=parsed_content.get('metadata', {}).get('quarter', form_data.get('quarter', '')),
            duration=parse_duration(parsed_content.get('metadata', {}).get('duration', form_data.get('duration', '0'))),
            population=parse_population(parsed_content.get('metadata', {}).get('class_size', form_data.get('population', '0'))),
            learning_objectives='\n'.join(parsed_content.get('learning_objectives', [])),
            subject_matter=format_subject_matter(parsed_content.get('subject_matter', {})),
            materials_needed='\n'.join(parsed_content.get('materials_needed', [])),
            introduction=parsed_content.get('procedure', {}).get('introduction', {}).get('content', ''),
            instruction=parsed_content.get('procedure', {}).get('instruction', {}).get('content', ''),
            application=parsed_content.get('procedure', {}).get('application', {}).get('content', ''),
            evaluation=parsed_content.get('procedure', {}).get('evaluation', {}).get('content', ''),
            assessment=parsed_content.get('procedure', {}).get('assessment', {}).get('content', ''),
            generated_content=generated_content,
            created_by=request.user
        )
        lesson_plan.save()
        
        # Clear the session data after saving
        if 'generated_lesson_plan' in request.session:
            del request.session['generated_lesson_plan']
        if 'parsed_lesson_plan' in request.session:
            del request.session['parsed_lesson_plan']
        if 'lesson_form_data' in request.session:
            del request.session['lesson_form_data']
        
        return JsonResponse({
            'success': True,
            'draft_id': lesson_plan.id,
            'message': 'Lesson plan saved as draft successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error saving lesson plan: {str(e)}'
        }, status=500)

def parse_duration(duration_str):
    """Parse duration string to minutes"""
    try:
        # Extract numbers from duration string
        numbers = re.findall(r'\d+', duration_str)
        if numbers:
            return int(numbers[0])
        return 0
    except (ValueError, TypeError):
        return 0

def parse_population(population_str):
    """Parse population string to integer"""
    try:
        # Extract numbers from population string
        numbers = re.findall(r'\d+', population_str)
        if numbers:
            return int(numbers[0])
        return 0
    except (ValueError, TypeError):
        return 0

def format_subject_matter(subject_matter_dict):
    """Format subject matter dictionary into a string"""
    parts = []
    if 'topic' in subject_matter_dict:
        parts.append(f"Topic: {subject_matter_dict['topic']}")
    if 'key_concepts' in subject_matter_dict:
        parts.append(f"Key Concepts: {subject_matter_dict['key_concepts']}")
    if 'vocabulary' in subject_matter_dict:
        parts.append(f"Vocabulary: {subject_matter_dict['vocabulary']}")
    return '\n'.join(parts)

@login_required
def draft_list(request):
    """Display list of saved drafts"""
    drafts = LessonPlan.objects.filter(created_by=request.user, status=LessonPlan.DRAFT).order_by('-created_at')
    return render(request, 'lessonGenerator/draft_list.html', {'drafts': drafts})

@login_required
def edit_draft(request, draft_id):
    """Edit a saved draft"""
    draft = get_object_or_404(LessonPlan, id=draft_id, created_by=request.user)
    
    if request.method == 'POST':
        # Update the draft with new data
        draft.title = request.POST.get('title', draft.title)
        draft.subject = request.POST.get('subject', draft.subject)
        draft.grade_level = request.POST.get('grade_level', draft.grade_level)
        draft.quarter = request.POST.get('quarter', draft.quarter)
        draft.duration = int(request.POST.get('duration', draft.duration))
        draft.population = int(request.POST.get('population', draft.population))
        draft.learning_objectives = request.POST.get('learning_objectives', draft.learning_objectives)
        draft.subject_matter = request.POST.get('subject_matter', draft.subject_matter)
        draft.materials_needed = request.POST.get('materials_needed', draft.materials_needed)
        draft.introduction = request.POST.get('introduction', draft.introduction)
        draft.instruction = request.POST.get('instruction', draft.instruction)
        draft.application = request.POST.get('application', draft.application)
        draft.evaluation = request.POST.get('evaluation', draft.evaluation)
        draft.assessment = request.POST.get('assessment', draft.assessment)
        draft.generated_content = request.POST.get('generated_content', draft.generated_content)
        draft.save()
        
        messages.success(request, 'Draft updated successfully!')
        return redirect('draft_list')
    
    return render(request, 'lessonGenerator/edit_draft.html', {'draft': draft})

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def regenerate_lesson_content(request):
    """Regenerate AI content based on edited form data"""
    try:
        # Check if Gemini is configured properly
        if model is None:
            return JsonResponse({
                'success': False,
                'error': 'AI service is not configured properly.'
            }, status=500)
            
        # Parse JSON data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data received.'
            }, status=400)
        
        # Format the prompt for the AI (same as before)
        prompt = f"""
        Create a comprehensive lesson plan based on these details:

        SUBJECT: {data.get('subject', '').strip()}
        GRADE LEVEL: {data.get('grade_level', '').strip()}
        QUARTER: {data.get('quarter', '').strip()}
        DURATION: {data.get('duration', '').strip()} minutes
        CLASS SIZE: {data.get('population', '').strip()} students
        LEARNING OBJECTIVES: {data.get('learning_objectives', '').strip()}
        SUBJECT MATTER: {data.get('subject_matter', '').strip()}
        MATERIALS NEEDED: {data.get('materials_needed', '').strip()}
        INTRODUCTION: {data.get('introduction', '').strip()}
        INSTRUCTION: {data.get('instruction', '').strip()}
        APPLICATION: {data.get('application', '').strip()}
        EVALUATION: {data.get('evaluation', '').strip()}
        ASSESSMENT: {data.get('assessment', '').strip()}

        Please generate a complete lesson plan using the specified format.
        """
        
        # Generate the lesson plan using Gemini
        try:
            response = model.generate_content([
                LESSON_PLANNER_SYSTEM_INSTRUCTION,
                prompt
            ])
            
            return JsonResponse({
                'success': True,
                'generated_content': response.text
            })
            
        except Exception as ai_error:
            return JsonResponse({
                'success': False,
                'error': f'AI service error: {str(ai_error)}'
            }, status=500)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)