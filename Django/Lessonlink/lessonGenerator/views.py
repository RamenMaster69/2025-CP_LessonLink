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

# Make sure this index function exists
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
            
            return JsonResponse({
                'success': True,
                'lesson_plan': response.text
            })
            
        except Exception as ai_error:
            return JsonResponse({
                'success': False,
                'error': f'AI service error: {str(ai_error)}'
            }, status=500)

        # After generating the lesson plan, save it as a draft
        if data.get('save_as_draft', False) and request.user.is_authenticated:
            lesson_plan = LessonPlan(
                title=f"{form_data['subject']} - {form_data['grade_level']}",
                subject=form_data['subject'],
                grade_level=form_data['grade_level'],
                quarter=form_data['quarter'],
                duration=int(form_data['duration']) if form_data['duration'].isdigit() else 0,
                population=int(form_data['population']) if form_data['population'].isdigit() else 0,
                learning_objectives=form_data['learning_objectives'],
                subject_matter=form_data['subject_matter'],
                materials_needed=form_data['materials_needed'],
                introduction=form_data['introduction'],
                instruction=form_data['instruction'],
                application=form_data['application'],
                evaluation=form_data['evaluation'],
                assessment=form_data['assessment'],
                generated_content=response.text,
                created_by=request.user
            )
            lesson_plan.save()
            
            return JsonResponse({
                'success': True,
                'lesson_plan': response.text,
                'draft_id': lesson_plan.id,
                'message': 'Lesson plan saved as draft successfully!'
            })
        else:
            return JsonResponse({
                'success': True,
                'lesson_plan': response.text
            })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)

def lesson_plan_result(request):
    """Render the lesson plan result page"""
    lesson_plan = request.GET.get('plan', '')
    draft_id = request.GET.get('draft_id', '')
    return render(request, 'lessonGenerator/lesson_plan.html', {
        'lesson_plan': lesson_plan,
        'draft_id': draft_id
    })

# ================================================================== SAVE AS DRAFT, THIS PART HERE =====================================================================================

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def save_lesson_plan(request):
    """Save the generated lesson plan as a draft with parsed procedure sections"""
    try:
        data = json.loads(request.body)
        
        # Parse procedure sections from generated content
        generated_content = data.get('generated_content', '')
        procedure_sections = parse_procedure_sections(generated_content)
        
        # Create a new LessonPlan instance
        lesson_plan = LessonPlan(
            title=data.get('title', 'Untitled Lesson Plan'),
            subject=data.get('subject', ''),
            grade_level=data.get('grade_level', ''),
            quarter=data.get('quarter', ''),
            duration=int(data.get('duration', 0)),
            population=int(data.get('population', 0)),
            learning_objectives=data.get('learning_objectives', ''),
            subject_matter=data.get('subject_matter', ''),
            materials_needed=data.get('materials_needed', ''),
            introduction=procedure_sections.get('introduction', {}).get('content', ''),
            instruction=procedure_sections.get('instruction', {}).get('content', ''),
            application=procedure_sections.get('application', {}).get('content', ''),
            evaluation=procedure_sections.get('evaluation', {}).get('content', ''),
            assessment=procedure_sections.get('assessment', {}).get('content', ''),
            generated_content=generated_content,
            created_by=request.user
        )
        lesson_plan.save()
        
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

def parse_procedure_sections(content):
    """Parse the lesson procedure sections from the generated content"""
    sections = {
        'introduction': {'time': '', 'content': ''},
        'instruction': {'time': '', 'content': ''},
        'application': {'time': '', 'content': ''},
        'evaluation': {'time': '', 'content': ''},
        'assessment': {'time': '', 'content': ''},
    }
    
    # Find the Lesson Procedure section
    procedure_match = re.search(r'## Lesson Procedure\s*\n(.*?)(?=##|$)', content, re.DOTALL | re.IGNORECASE)
    if not procedure_match:
        return sections
    
    procedure_content = procedure_match.group(1)
    
    # Parse each subsection
    subsection_patterns = {
        'introduction': r'### A\. Introduction\s*\(([^)]+)\)\s*\n(.*?)(?=###|$)',
        'instruction': r'### B\. Instruction/Direct Teaching\s*\(([^)]+)\)\s*\n(.*?)(?=###|$)',
        'application': r'### C\. Guided Practice/Application\s*\(([^)]+)\)\s*\n(.*?)(?=###|$)',
        'evaluation': r'### D\. Independent Practice/Evaluation\s*\(([^)]+)\)\s*\n(.*?)(?=###|$)',
        'assessment': r'### E\. Assessment\s*\(([^)]+)\)\s*\n(.*?)(?=###|$)',
    }
    
    for section, pattern in subsection_patterns.items():
        match = re.search(pattern, procedure_content, re.DOTALL | re.IGNORECASE)
        if match:
            sections[section] = {
                'time': match.group(1).strip(),
                'content': match.group(2).strip()
            }
    
    return sections

@login_required
def draft_list(request):
    """Display list of saved drafts"""
    drafts = LessonPlan.objects.filter(created_by=request.user, status=LessonPlan.DRAFT).order_by('-created_at')
    return render(request, 'lessonGenerator/draft_list.html', {'drafts': drafts})

# views.py
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

# views.py
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
