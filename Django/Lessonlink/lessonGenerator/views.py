import json
import google.generativeai as genai
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

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
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)

def lesson_plan_result(request):
    """Render the lesson plan result page"""
    lesson_plan = request.GET.get('plan', '')
    return render(request, 'lessonGenerator/lesson_plan.html', {'lesson_plan': lesson_plan})
