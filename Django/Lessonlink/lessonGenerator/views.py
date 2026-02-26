import json
import google.generativeai as genai
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
import re
from .models import LessonPlan, LessonPlanSubmission
from .ai_instructions import (
    LESSON_PLANNER_SYSTEM_INSTRUCTION, 
    EXEMPLAR_REFERENCE_INSTRUCTION,
    INTELLIGENCE_ADAPTATION_INSTRUCTION,
    get_system_instruction
)
import markdown
from .models import WeeklyLessonPlan, LessonPlanSubmission
from .ai_instructions import get_weekly_system_instruction, WEEKLY_LESSON_PLANNER_INSTRUCTION

# Configure the Gemini API
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    print(f"Gemini configuration error: {e}")
    model = None

def lesson_ai(request):
    """Render the main page with the lesson plan form"""
    return render(request, 'lessonGenerator/lesson_ai.html')

def analyze_input_relation(user_inputs, exemplar_content, exemplar_name):
    """
    Analyze if user inputs are related to the selected exemplar
    Returns: (is_related: bool, explanation: str, confidence_score: float)
    """
    try:
        if not exemplar_content or not user_inputs:
            return True, "No exemplar selected", 1.0
        
        # Prepare analysis prompt
        analysis_prompt = f"""
        Analyze the relationship between the user's lesson plan inputs and the selected exemplar.
        
        USER INPUTS:
        Subject: {user_inputs.get('subject', '')}
        Grade Level: {user_inputs.get('grade_level', '')}
        Learning Objectives: {user_inputs.get('learning_objectives', '')}
        Subject Matter: {user_inputs.get('subject_matter', '')}
        
        SELECTED EXEMPLAR: {exemplar_name}
        EXEMPLAR CONTENT (first 2000 chars): {exemplar_content[:2000]}
        
        ANALYSIS TASK:
        1. Determine if the user's inputs are related to the exemplar
        2. Check for subject alignment
        3. Check for grade level appropriateness
        4. Check if learning objectives are compatible with exemplar content
        5. Check if subject matter aligns with exemplar focus
        
        RELATIONSHIP CRITERIA:
        - DIRECT RELATION: Same subject area, similar topics, compatible grade level
        - INDIRECT RELATION: Different but related subjects, transferable concepts
        - UNRELATED: Completely different subjects/topics, incompatible content
        
        Return ONLY a JSON object with this exact structure:
        {{
            "is_related": true/false,
            "confidence_score": 0.0-1.0,
            "explanation": "Detailed explanation of the relationship analysis",
            "specific_issues": ["List of specific issues if unrelated"],
            "suggestions": ["Suggestions for better alignment if unrelated"]
        }}
        
        Be strict but fair. Only mark as unrelated if there's a clear mismatch that would make
        the exemplar useless as a reference.
        """
        
        response = model.generate_content([
            "You are an educational content analyst. Analyze the relationship between lesson plan inputs and exemplars. Return only JSON.",
            analysis_prompt
        ])
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            analysis_result = json.loads(json_match.group())
            return (
                analysis_result.get('is_related', True),
                analysis_result.get('explanation', ''),
                analysis_result.get('confidence_score', 0.0)
            )
        else:
            # If analysis fails, default to allowing (but log warning)
            print("Failed to parse relationship analysis, defaulting to allowed")
            return True, "Analysis failed, proceeding with caution", 0.5
            
    except Exception as e:
        print(f"Relationship analysis error: {str(e)}")
        return True, f"Analysis error: {str(e)}", 0.5

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
            print("Received data:", data)  # Debugging
        except json.JSONDecodeError as e:
            print("JSON decode error:", e)  # Debugging
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data received.'
            }, status=400)
        
        # Extract form data with validation - INCLUDING INTELLIGENCE TYPE
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
            'duration': data.get('duration', '60').strip(),  # Default to 60 minutes
            'population': data.get('population', '30').strip(),  # Default to 30 students
            'learning_objectives': data.get('learning_objectives', '').strip(),
            'subject_matter': data.get('subject_matter', '').strip(),
            'materials_needed': data.get('materials_needed', '').strip(),
            'introduction': data.get('introduction', '').strip(),
            'instruction': data.get('instruction', '').strip(),
            'application': data.get('application', '').strip(),
            'evaluation': data.get('evaluation', '').strip(),
            'assessment': data.get('assessment', '').strip(),
            'selected_exemplar': data.get('selected_exemplar', '').strip(),
            'intelligence_type': data.get('intelligence_type', 'comprehensive').strip(),  # NEW FIELD
        }
        
        print("Form data prepared:", form_data)  # Debugging
        print("Intelligence type:", form_data['intelligence_type'])  # Debugging
        
        # Get exemplar content if selected
        exemplar_content = ""
        exemplar_name = ""
        if form_data['selected_exemplar']:
            try:
                from lesson.models import Exemplar
                exemplar = Exemplar.objects.get(id=form_data['selected_exemplar'])
                exemplar_content = exemplar.extracted_text
                exemplar_name = exemplar.name
                print(f"Exemplar content loaded: {len(exemplar_content)} characters from {exemplar_name}")  # Debugging
                
                # REAL-TIME INPUT VALIDATION: Check if inputs are related to exemplar
                print("Analyzing input-exemplar relationship...")  # Debugging
                is_related, explanation, confidence = analyze_input_relation(
                    form_data, 
                    exemplar_content, 
                    exemplar_name
                )
                
                print(f"Relationship analysis: is_related={is_related}, confidence={confidence}")  # Debugging
                
                if not is_related:
                    # Inputs are not related to exemplar - return error
                    return JsonResponse({
                        'success': False,
                        'error': f'INPUT VALIDATION ERROR: Your lesson plan inputs are not sufficiently related to the selected exemplar "{exemplar_name}".\n\n'
                                f'Analysis: {explanation}\n\n'
                                f'Please either:\n'
                                f'1. Choose a different exemplar that matches your subject/topic\n'
                                f'2. Adjust your lesson plan inputs to better align with the exemplar\n'
                                f'3. Deselect the exemplar if you want to create a lesson plan without reference',
                        'validation_error': True,
                        'exemplar_name': exemplar_name,
                        'confidence_score': confidence,
                        'analysis_explanation': explanation
                    }, status=400)
                
                print(f"Inputs validated: {explanation}")  # Debugging
                    
            except Exemplar.DoesNotExist:
                print("Selected exemplar not found")
            except Exception as e:
                print(f"Error loading exemplar: {str(e)}")
        
        # Format the prompt for the AI - INCLUDING INTELLIGENCE TYPE
        prompt = f"""
        Generate this as a complete MATATAG-aligned lesson plan following DepEd Philippines MATATAG Curriculum standards.
        
        **INTELLIGENCE TYPE FOCUS:** {form_data['intelligence_type'].upper()}
        
        SUBJECT: {form_data['subject']}
        GRADE LEVEL: {form_data['grade_level']}
        QUARTER: {form_data['quarter'] or 'Not specified'}
        DURATION: {form_data['duration']} minutes
        CLASS SIZE: {form_data['population']} students
        
        LEARNING OBJECTIVES:
        {form_data['learning_objectives']}
        
        SUBJECT MATTER: {form_data['subject_matter'] or 'To be developed based on MELC standards'}
        MATERIALS NEEDED: {form_data['materials_needed'] or 'To be specified based on lesson requirements'}
        INTRODUCTION: {form_data['introduction'] or 'To be developed based on MELC alignment'}
        INSTRUCTION: {form_data['instruction'] or 'To be developed based on direct teaching methods'}
        APPLICATION: {form_data['application'] or 'To be developed for guided practice'}
        EVALUATION: {form_data['evaluation'] or 'To be developed for independent practice'}
        ASSESSMENT: {form_data['assessment'] or 'To be developed for formal assessment'}

        {'REFERENCE EXEMPLAR: ' + exemplar_name if exemplar_name else ''}
        {'EXEMPLAR CONTENT FOR REFERENCE: ' + exemplar_content[:2000] + '...' if exemplar_content else ''}

        Generate this as a complete MELC-aligned lesson plan following DepEd Philippines standards.
        Use the learning objectives provided to create specific, measurable outcomes.
        
        **INTELLIGENCE TYPE ADAPTATION REQUIREMENTS:**
        1. Design activities specifically aligned with the {form_data['intelligence_type']} intelligence focus
        2. Include assessment methods appropriate for measuring the targeted intelligence
        3. Provide clear differentiation strategies for the selected intelligence focus
        4. Maintain MELC alignment while incorporating intelligence adaptation
        
        {'Use the reference exemplar as a guide for structure, depth, and quality standards while maintaining originality.' if exemplar_content else ''}
        """
        
        print("Sending prompt to AI")  # Debugging
        print(f"Exemplar provided: {bool(exemplar_content)}")  # Debugging
        print(f"Intelligence type: {form_data['intelligence_type']}")  # Debugging
        
        # Generate the lesson plan using Gemini
        try:
            # Check if exemplar is provided
            has_exemplar = bool(form_data['selected_exemplar'] and exemplar_content)
            
            # Use appropriate system instruction with intelligence type
            system_instruction = get_system_instruction(
                has_exemplar=has_exemplar,
                intelligence_type=form_data['intelligence_type']
            )
            
            print(f"Using system instruction with intelligence type: {form_data['intelligence_type']}")  # Debugging
            
            response = model.generate_content([
                system_instruction,
                prompt
            ])
            
            print("AI response received:", response.text[:200] + "...")  # Debugging first 200 chars
            
            # Try to parse the response as JSON
            try:
                # Extract JSON from the response (Gemini might add some text around it)
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    lesson_data = json.loads(json_match.group())
                    print("JSON parsed successfully")  # Debugging
                    
                    # Store both the structured data and markdown in session
                    request.session['generated_lesson_plan'] = lesson_data.get('markdown_output', '')
                    request.session['parsed_lesson_plan'] = lesson_data
                    request.session['lesson_form_data'] = form_data
                    request.session.modified = True
                    
                    return JsonResponse({
                        'success': True,
                        'lesson_plan': lesson_data.get('markdown_output', ''),
                        'exemplar_used': has_exemplar,
                        'intelligence_type': form_data['intelligence_type'],
                        'exemplar_id': form_data['selected_exemplar'] if has_exemplar else None,
                        'exemplar_name': exemplar_name if has_exemplar else None,
                        'validation_passed': True if has_exemplar else None
                    })
                else:
                    # Fallback: if no JSON found, treat as markdown
                    print("No JSON found in response, using fallback")  # Debugging
                    request.session['generated_lesson_plan'] = response.text
                    request.session['lesson_form_data'] = form_data
                    request.session.modified = True
                    
                    return JsonResponse({
                        'success': True,
                        'lesson_plan': response.text,
                        'exemplar_used': has_exemplar,
                        'intelligence_type': form_data['intelligence_type'],
                        'exemplar_id': form_data['selected_exemplar'] if has_exemplar else None,
                        'exemplar_name': exemplar_name if has_exemplar else None,
                        'validation_passed': True if has_exemplar else None
                    })
                    
            except json.JSONDecodeError as json_error:
                # If JSON parsing fails, fall back to markdown
                print(f"JSON parsing error: {json_error}")  # Debugging
                request.session['generated_lesson_plan'] = response.text
                request.session['lesson_form_data'] = form_data
                request.session.modified = True
                
                return JsonResponse({
                    'success': True,
                    'lesson_plan': response.text,
                    'exemplar_used': has_exemplar,
                    'intelligence_type': form_data['intelligence_type'],
                    'exemplar_id': form_data['selected_exemplar'] if has_exemplar else None,
                    'exemplar_name': exemplar_name if has_exemplar else None,
                    'validation_passed': True if has_exemplar else None
                })
            
        except Exception as ai_error:
            print(f"AI service error: {str(ai_error)}")  # Debugging
            return JsonResponse({
                'success': False,
                'error': f'AI service error: {str(ai_error)}'
            }, status=500)
        
    except Exception as e:
        print(f"Server error: {str(e)}")  # Debugging
        import traceback
        traceback.print_exc()  # This will print the full traceback to console
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)

def lesson_plan_result(request):
    """Render the lesson plan result page"""
    lesson_plan = request.session.get('generated_lesson_plan', '')
    form_data = request.session.get('lesson_form_data', {})
    
    if not lesson_plan:
        messages.error(request, 'No lesson plan found. Please generate a lesson plan first.')
        return redirect('lesson_ai')
    
    # Process markdown in the view
    import markdown
    lesson_plan_html = markdown.markdown(lesson_plan, extensions=['extra', 'nl2br'])
    
    return render(request, 'lessonGenerator/lesson_plan.html', {
        'lesson_plan': lesson_plan_html,
        'intelligence_type': form_data.get('intelligence_type', 'comprehensive')
    })

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def save_lesson_plan(request):
    """Save the generated lesson plan as a draft with parsed sections including MELC data"""
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
        
        # Check if user is a department head for auto-approval
        is_department_head = hasattr(request.user, 'role') and request.user.role == 'Department Head'
        
        # If we have parsed JSON content, use it
        if parsed_content and isinstance(parsed_content, dict):
            # Use the parsed JSON data
            metadata = parsed_content.get('metadata', {})
            procedure = parsed_content.get('procedure', {})
            subject_matter = parsed_content.get('subject_matter', {})
            melc_alignment = parsed_content.get('melc_alignment', {})
            integration = parsed_content.get('integration', {})
            intelligence_adaptation = parsed_content.get('intelligence_adaptation', {})
            
            lesson_plan = LessonPlan(
                title=parsed_content.get('title', f"{metadata.get('subject', 'Untitled')} - {metadata.get('grade_level', '')}"),
                subject=metadata.get('subject', form_data.get('subject', '')),
                grade_level=metadata.get('grade_level', form_data.get('grade_level', '')),
                quarter=metadata.get('quarter', form_data.get('quarter', '')),
                duration=parse_duration(metadata.get('duration', form_data.get('duration', '0'))),
                population=parse_population(metadata.get('class_size', form_data.get('population', '0'))),
                learning_objectives='\n'.join(parsed_content.get('learning_objectives', [])),
                subject_matter=format_subject_matter(subject_matter),
                materials_needed='\n'.join(parsed_content.get('materials_needed', [])),
                introduction=procedure.get('introduction', {}).get('content', ''),
                instruction=procedure.get('instruction', {}).get('content', ''),
                application=procedure.get('application', {}).get('content', ''),
                evaluation=procedure.get('evaluation', {}).get('content', ''),
                assessment=procedure.get('assessment', {}).get('content', ''),
                generated_content=generated_content,
                created_by=request.user,
                # Intelligence type field - NEW
                intelligence_type=form_data.get('intelligence_type', 'comprehensive'),
                # MELC Alignment fields
                melc_code=melc_alignment.get('melc_code', ''),
                content_standard=melc_alignment.get('content_standard', ''),
                performance_standard=melc_alignment.get('performance_standard', ''),
                learning_competency=melc_alignment.get('learning_competency', ''),
                # Integration fields
                values_integration=integration.get('values_education', ''),
                cross_curricular=integration.get('cross_curricular', ''),
                # Auto-approve for department heads
                status=LessonPlan.FINAL if is_department_head else LessonPlan.DRAFT,
                auto_approved=is_department_head
            )
        else:
            # Fallback: if no parsed JSON, use form data with empty procedure sections
            lesson_plan = LessonPlan(
                title=f"{form_data.get('subject', 'Untitled')} - {form_data.get('grade_level', '')}",
                subject=form_data.get('subject', ''),
                grade_level=form_data.get('grade_level', ''),
                quarter=form_data.get('quarter', ''),
                duration=parse_duration(form_data.get('duration', '0')),
                population=parse_population(form_data.get('population', '0')),
                learning_objectives=form_data.get('learning_objectives', ''),
                subject_matter=form_data.get('subject_matter', ''),
                materials_needed=form_data.get('materials_needed', ''),
                introduction=form_data.get('introduction', ''),
                instruction=form_data.get('instruction', ''),
                application=form_data.get('application', ''),
                evaluation=form_data.get('evaluation', ''),
                assessment=form_data.get('assessment', ''),
                generated_content=generated_content,
                created_by=request.user,
                # Intelligence type field - NEW
                intelligence_type=form_data.get('intelligence_type', 'comprehensive'),
                # Auto-approve for department heads
                status=LessonPlan.FINAL if is_department_head else LessonPlan.DRAFT,
                auto_approved=is_department_head
            )
        
        lesson_plan.save()
        
        # Clear the session data after saving
        if 'generated_lesson_plan' in request.session:
            del request.session['generated_lesson_plan']
        if 'parsed_lesson_plan' in request.session:
            del request.session['parsed_lesson_plan']
        if 'lesson_form_data' in request.session:
            del request.session['lesson_form_data']
        
        message = 'Lesson plan saved as draft successfully!'
        if is_department_head:
            message = 'Lesson plan created and automatically approved!'
        
        return JsonResponse({
            'success': True,
            'draft_id': lesson_plan.id,
            'message': message,
            'intelligence_type': form_data.get('intelligence_type', 'comprehensive'),
            'auto_approved': is_department_head,
            'user_role': request.user.role if hasattr(request.user, 'role') else 'Teacher',
            'redirect_url': '/drafts/department-head/' if is_department_head else '/drafts/'
        })
        
    except Exception as e:
        import traceback
        print(f"Error saving lesson plan: {str(e)}")
        print(traceback.format_exc())
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
    if isinstance(subject_matter_dict, str):
        return subject_matter_dict
    
    parts = []
    if subject_matter_dict.get('topic'):
        parts.append(f"Topic: {subject_matter_dict['topic']}")
    if subject_matter_dict.get('key_concepts'):
        parts.append(f"Key Concepts: {subject_matter_dict['key_concepts']}")
    if subject_matter_dict.get('vocabulary'):
        parts.append(f"Vocabulary: {subject_matter_dict['vocabulary']}")
    if subject_matter_dict.get('references'):
        parts.append(f"References: {subject_matter_dict['references']}")
    return '\n'.join(parts)

@login_required
def draft_list(request):
    """Display list of saved drafts with submission status"""
    # Get all drafts for the user
    drafts = LessonPlan.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Prefetch related submissions to avoid N+1 queries
    draft_ids = [draft.id for draft in drafts]
    
    # Get all submissions for these drafts in one query
    submissions = LessonPlanSubmission.objects.filter(
        lesson_plan_id__in=draft_ids
    ).order_by('lesson_plan_id', '-submission_date')
    
    # Create a dictionary mapping draft ID to latest submission
    latest_submissions = {}
    for submission in submissions:
        if submission.lesson_plan_id not in latest_submissions:
            latest_submissions[submission.lesson_plan_id] = submission
    
    # Create a list of tuples with draft and its latest submission
    draft_data = []
    for draft in drafts:
        draft_data.append({
            'draft': draft,
            'latest_submission': latest_submissions.get(draft.id)
        })
    
    # Count by status for the summary cards
    draft_count = LessonPlan.objects.filter(
        created_by=request.user, 
        status=LessonPlan.DRAFT
    ).count()
    
    # Count by intelligence type for insights
    intelligence_counts = {}
    for intelligence_type, display_name in LessonPlan.INTELLIGENCE_TYPE_CHOICES:
        count = LessonPlan.objects.filter(
            created_by=request.user,
            intelligence_type=intelligence_type
        ).count()
        if count > 0:
            intelligence_counts[intelligence_type] = {
                'display': display_name,
                'count': count
            }
    
    # Count submissions by status for the current user
    user_submissions = LessonPlanSubmission.objects.filter(
        submitted_by=request.user
    )
    
    submitted_count = user_submissions.filter(status='submitted').count()
    approved_count = user_submissions.filter(status='approved').count()
    revision_count = user_submissions.filter(status='needs_revision').count()
    rejected_count = user_submissions.filter(status='rejected').count()
    
    return render(request, 'lessonGenerator/draft_list.html', {
        'draft_data': draft_data,
        'draft_count': draft_count,
        'submitted_count': submitted_count,
        'approved_count': approved_count,
        'revision_count': revision_count,
        'rejected_count': rejected_count,
        'intelligence_counts': intelligence_counts  # NEW: Add intelligence insights
    })

@login_required
def edit_draft(request, draft_id):
    """Edit a saved draft"""
    draft = get_object_or_404(LessonPlan, id=draft_id, created_by=request.user)
    
    if request.method == 'POST':
        # Update the draft with new data including intelligence type
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
        
        # Update intelligence type - NEW
        draft.intelligence_type = request.POST.get('intelligence_type', draft.intelligence_type)
        
        # Update MELC fields if provided
        draft.melc_code = request.POST.get('melc_code', draft.melc_code)
        draft.content_standard = request.POST.get('content_standard', draft.content_standard)
        draft.performance_standard = request.POST.get('performance_standard', draft.performance_standard)
        draft.learning_competency = request.POST.get('learning_competency', draft.learning_competency)
        draft.values_integration = request.POST.get('values_integration', draft.values_integration)
        draft.cross_curricular = request.POST.get('cross_curricular', draft.cross_curricular)
        
        draft.save()
        
        messages.success(request, 'Draft updated successfully!')
        
        # Redirect based on user role
        if hasattr(request.user, 'role') and request.user.role == 'Department Head':
            return redirect('department_head_drafts')
        else:
            return redirect('draft_list')
    
    return render(request, 'lessonGenerator/edit_draft.html', {
        'draft': draft,
        'intelligence_choices': LessonPlan.INTELLIGENCE_TYPE_CHOICES  # Pass choices to template
    })

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def regenerate_lesson_content(request):
    """Regenerate AI content based on edited form data including intelligence type"""
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
        
        # Get intelligence type from data
        intelligence_type = data.get('intelligence_type', 'comprehensive')
        
        # Format the prompt for the AI with MELC focus and intelligence type
        prompt = f"""
        Create a comprehensive MELC-aligned lesson plan with {intelligence_type} intelligence focus.

        INTELLIGENCE TYPE: {intelligence_type.upper()}
        
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

        Generate this as a complete MELC-aligned lesson plan following DepEd Philippines standards.
        Focus on {intelligence_type} intelligence development while maintaining curriculum alignment.
        Include appropriate MELC codes, content standards, performance standards, and learning competencies.
        Design activities specifically for {intelligence_type} intelligence development.
        """
        
        # Generate the lesson plan using Gemini with intelligence type
        try:
            system_instruction = get_system_instruction(
                has_exemplar=False,
                intelligence_type=intelligence_type
            )
            
            response = model.generate_content([
                system_instruction,
                prompt
            ])
            
            return JsonResponse({
                'success': True,
                'generated_content': response.text,
                'intelligence_type': intelligence_type
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

@login_required
def view_draft(request, draft_id):
    """View a lesson draft in read-only format"""
    draft = get_object_or_404(LessonPlan, id=draft_id, created_by=request.user)
    
    # Get submission status if exists
    latest_submission = LessonPlanSubmission.objects.filter(
        lesson_plan=draft
    ).order_by('-submission_date').first()
    
    # Get intelligence type display name
    intelligence_display = dict(LessonPlan.INTELLIGENCE_TYPE_CHOICES).get(
        draft.intelligence_type, 
        draft.intelligence_type
    )
    
    return render(request, 'lessonGenerator/view_draft.html', {
        'draft': draft,
        'latest_submission': latest_submission,
        'intelligence_display': intelligence_display
    })

@login_required
def department_head_drafts(request):
    """Display list of department head's lesson plans (auto-approved)"""
    if hasattr(request.user, 'role') and request.user.role != 'Department Head':
        messages.error(request, "Access denied. Department heads only.")
        return redirect('draft_list')
    
    # Get all approved lesson plans for the department head
    approved_plans = LessonPlan.objects.filter(
        created_by=request.user, 
        status=LessonPlan.FINAL,
        auto_approved=True
    ).order_by('-created_at')
    
    # Get drafts if any
    draft_plans = LessonPlan.objects.filter(
        created_by=request.user,
        status=LessonPlan.DRAFT
    ).order_by('-created_at')
    
    # Count by intelligence type for insights
    intelligence_counts = {}
    for intelligence_type, display_name in LessonPlan.INTELLIGENCE_TYPE_CHOICES:
        count = LessonPlan.objects.filter(
            created_by=request.user,
            intelligence_type=intelligence_type
        ).count()
        if count > 0:
            intelligence_counts[intelligence_type] = {
                'display': display_name,
                'count': count
            }
    
    return render(request, 'lessonGenerator/department_head_drafts.html', {
        'approved_plans': approved_plans,
        'draft_plans': draft_plans,
        'approved_count': approved_plans.count(),
        'draft_count': draft_plans.count(),
        'intelligence_counts': intelligence_counts,
        'is_department_head': True
    })

@csrf_exempt
@require_http_methods(["POST"])
def get_ai_suggestions(request):
    """Generate AI suggestions for specific lesson plan sections including intelligence type"""
    try:
        if model is None:
            return JsonResponse({
                'success': False,
                'error': 'AI service not configured'
            }, status=500)
            
        data = json.loads(request.body)
        section = data.get('section')
        form_data = data.get('form_data', {})
        
        if not section:
            return JsonResponse({
                'success': False,
                'error': 'Section parameter required'
            }, status=400)
        
        # Get intelligence type from form data
        intelligence_type = form_data.get('intelligence_type', 'comprehensive')
        
        # Create context-aware prompt for suggestions with MELC and intelligence focus
        prompt = f"""
        Analyze this lesson plan context and provide 3 targeted MELC-aligned suggestions for the {section} section.
        
        INTELLIGENCE TYPE FOCUS: {intelligence_type.upper()}
        
        CONTEXT:
        Subject: {form_data.get('subject', 'Not specified')}
        Grade Level: {form_data.get('gradeLevel', 'Not specified')}
        Learning Objectives: {form_data.get('learningObjectives', 'Not specified')}
        Subject Matter: {form_data.get('subjectMatter', 'Not specified')}
        
        Provide 3 specific, actionable MELC-aligned suggestions for the {section} section that are appropriate for this context.
        Focus on DepEd Philippines standards and {intelligence_type} intelligence development.
        
        For {intelligence_type} intelligence, focus on:
        {get_intelligence_focus_description(intelligence_type)}
        
        Return ONLY a JSON array with this exact format:
        [
            {{
                "title": "MELC-aligned suggestion title",
                "description": "Detailed suggestion description with {intelligence_type} intelligence focus",
                "example": "Concrete example or implementation idea aligned with DepEd standards",
                "intelligence_connection": "How this suggestion develops {intelligence_type} intelligence"
            }}
        ]
        """
        
        response = model.generate_content([
            f"You are an expert educational consultant specialized in DepEd Philippines curriculum and multiple intelligence theory. Provide specific, practical MELC-aligned suggestions for lesson plan sections with {intelligence_type} intelligence focus.",
            prompt
        ])
        
        # Extract JSON from response
        import re
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_match:
            suggestions = json.loads(json_match.group())
        else:
            # Fallback if no JSON found
            suggestions = [{
                "title": f"{intelligence_type.upper()} Intelligence Suggestion",
                "description": response.text[:200] + "...",
                "example": "Based on DepEd curriculum standards and intelligence development",
                "intelligence_connection": f"Develops {intelligence_type} intelligence through targeted activities"
            }]
        
        return JsonResponse({
            'success': True,
            'suggestions': suggestions,
            'intelligence_type': intelligence_type
        })
        
    except Exception as e:
        print(f"AI suggestions error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Suggestion generation failed: {str(e)}'
        }, status=500)

def get_intelligence_focus_description(intelligence_type):
    """Get description for each intelligence type focus"""
    descriptions = {
        'comprehensive': "Balanced approach incorporating all intelligence types: cognitive tasks for logical thinking, emotional tasks for self-awareness, social tasks for collaboration, and resilience tasks for perseverance.",
        'cognitive': "Emphasize logical, mathematical, and analytical intelligence: problem-solving, pattern recognition, critical analysis, and logical reasoning activities.",
        'emotional': "Focus on emotional awareness and management: self-reflection, emotion identification, empathy development, and emotional regulation exercises.",
        'social': "Develop interpersonal and communication skills: collaboration, teamwork, communication exercises, and peer interaction activities.",
        'resilience': "Build perseverance and adaptability: challenging tasks, growth mindset activities, failure analysis, and stress management exercises.",
        'differentiated': "Provide varied activities for different intelligence types: tiered activities with clear intelligence labeling and multiple pathways for learning."
    }
    return descriptions.get(intelligence_type, "Balanced intelligence development approach.")

# Helper function for intelligence type analytics
@login_required
def intelligence_type_analytics(request):
    """Show analytics for intelligence type usage"""
    if hasattr(request.user, 'role') and request.user.role != 'Department Head':
        messages.error(request, "Access denied. Department heads only.")
        return redirect('draft_list')
    
    # Get all lesson plans in the department
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Get users in the same department as the department head
    department_users = User.objects.filter(
        department=request.user.department,
        school=request.user.school
    )
    
    # Get lesson plans by intelligence type
    intelligence_stats = {}
    total_plans = 0
    
    for intelligence_type, display_name in LessonPlan.INTELLIGENCE_TYPE_CHOICES:
        count = LessonPlan.objects.filter(
            created_by__in=department_users,
            intelligence_type=intelligence_type
        ).count()
        
        intelligence_stats[intelligence_type] = {
            'display': display_name,
            'count': count,
            'percentage': 0
        }
        total_plans += count
    
    # Calculate percentages
    for intelligence_type in intelligence_stats:
        if total_plans > 0:
            intelligence_stats[intelligence_type]['percentage'] = round(
                (intelligence_stats[intelligence_type]['count'] / total_plans) * 100, 1
            )
    
    # Get most popular intelligence type by subject
    subject_intelligence = {}
    subjects = LessonPlan.objects.filter(
        created_by__in=department_users
    ).values_list('subject', flat=True).distinct()
    
    for subject in subjects:
        subject_stats = {}
        for intelligence_type, display_name in LessonPlan.INTELLIGENCE_TYPE_CHOICES:
            count = LessonPlan.objects.filter(
                created_by__in=department_users,
                subject=subject,
                intelligence_type=intelligence_type
            ).count()
            if count > 0:
                subject_stats[intelligence_type] = {
                    'display': display_name,
                    'count': count
                }
        
        if subject_stats:
            # Find most used intelligence type for this subject
            most_used = max(subject_stats.items(), key=lambda x: x[1]['count'])
            subject_intelligence[subject] = {
                'most_used': most_used[0],
                'display': most_used[1]['display'],
                'count': most_used[1]['count'],
                'all_stats': subject_stats
            }
    
    return render(request, 'lessonGenerator/intelligence_analytics.html', {
        'intelligence_stats': intelligence_stats,
        'total_plans': total_plans,
        'subject_intelligence': subject_intelligence,
        'department_name': request.user.department if hasattr(request.user, 'department') else 'Your Department'
    })

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def delete_draft(request, draft_id):
    """Delete a lesson draft"""
    try:
        draft = get_object_or_404(LessonPlan, id=draft_id, created_by=request.user)
        
        # Check if there are any submissions (optional: you might want to prevent deletion if submitted)
        submissions = LessonPlanSubmission.objects.filter(lesson_plan=draft)
        
        # Delete the draft
        draft.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Lesson plan deleted successfully!'
        })
        
    except LessonPlan.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Lesson plan not found or you do not have permission to delete it.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error deleting lesson plan: {str(e)}'
        }, status=500)
        
        
@csrf_exempt
@require_http_methods(["POST"])
def check_exemplar_compatibility(request):
    """Quick compatibility check between subject and exemplar"""
    try:
        data = json.loads(request.body)
        subject = data.get('subject', '').strip()
        exemplar_id = data.get('exemplar_id', '').strip()
        
        if not subject or not exemplar_id:
            return JsonResponse({
                'compatible': True,
                'message': 'Insufficient data for compatibility check'
            })
        
        # Get exemplar
        from lesson.models import Exemplar
        try:
            exemplar = Exemplar.objects.get(id=exemplar_id)
            
            # Simple keyword-based compatibility check
            subject_lower = subject.lower()
            exemplar_text_lower = exemplar.extracted_text.lower() if exemplar.extracted_text else ""
            
            # Check for subject-related keywords
            subject_keywords = {
                'mathematics': ['math', 'mathematics', 'algebra', 'geometry', 'calculus', 'numbers'],
                'science': ['science', 'biology', 'chemistry', 'physics', 'experiment', 'lab'],
                'english': ['english', 'grammar', 'writing', 'literature', 'reading', 'comprehension'],
                'araling panlipunan': ['history', 'social studies', 'culture', 'government', 'geography'],
                'mapeh': ['music', 'arts', 'pe', 'physical education', 'health'],
                'tle': ['technology', 'livelihood', 'education', 'technical', 'vocational'],
                'filipino': ['filipino', 'tagalog', 'wika', 'panitikan']
            }
            
            # Determine compatibility
            compatible = False
            for key, keywords in subject_keywords.items():
                if key in subject_lower or any(kw in subject_lower for kw in keywords):
                    # Check if exemplar contains related keywords
                    if any(kw in exemplar_text_lower for kw in keywords):
                        compatible = True
                        break
            
            return JsonResponse({
                'compatible': compatible,
                'subject': subject,
                'exemplar_name': exemplar.name,
                'message': 'Compatible' if compatible else 'Potential mismatch detected'
            })
            
        except Exemplar.DoesNotExist:
            return JsonResponse({
                'compatible': True,
                'message': 'Exemplar not found'
            })
            
    except Exception as e:
        return JsonResponse({
            'compatible': True,
            'message': f'Error checking compatibility: {str(e)}'
        })

def lesson_ai_weekly(request):
    """Render the weekly lesson plan form"""
    return render(request, 'lessonGenerator/lesson_ai_weekly.html')


@csrf_exempt
@require_http_methods(["POST"])
def generate_weekly_lesson_plan(request):
    """
    Generate a weekly lesson plan using AI
    Implements same input validation as lesson_ai.html
    """
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
            print("Weekly plan data received:", data)
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data received.'
            }, status=400)
        
        # Validate required fields
        required_fields = ['subject', 'grade_level', 'week', 'quarter']
        for field in required_fields:
            if field not in data or not data.get(field, '').strip():
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Extract form data
        form_data = {
            'title': data.get('title', '').strip(),
            'subject': data.get('subject', '').strip(),
            'grade_level': data.get('grade_level', '').strip(),
            'week': data.get('week', '').strip(),
            'quarter': data.get('quarter', '').strip(),
            'exemplar_id': data.get('exemplar_id', '').strip(),
            'theme': data.get('theme', '').strip(),
            'content_standards': data.get('content_standards', '').strip(),
            'performance_standards': data.get('performance_standards', '').strip(),
            'objectives': data.get('objectives', {}),
            'intelligence_type': data.get('intelligence_type', 'comprehensive'),
            'approach': data.get('approach', '').strip(),
        }
        
        # Validate daily objectives
        objectives = form_data['objectives']
        if not isinstance(objectives, dict):
            objectives = {}
        
        # Check if at least some objectives are provided
        has_objectives = any(objectives.get(day, '').strip() for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'])
        if not has_objectives:
            return JsonResponse({
                'success': False,
                'error': 'Please provide at least one daily learning objective.'
            }, status=400)
        
        # Get exemplar content if selected
        exemplar_content = ""
        exemplar_name = ""
        if form_data['exemplar_id']:
            try:
                from lesson.models import Exemplar
                exemplar = Exemplar.objects.get(id=form_data['exemplar_id'])
                exemplar_content = exemplar.extracted_text
                exemplar_name = exemplar.name
                print(f"Weekly exemplar loaded: {exemplar_name}")
                
                # REAL-TIME INPUT VALIDATION: Check if inputs are related to exemplar
                print("Analyzing weekly plan inputs against exemplar...")
                is_related, explanation, confidence = analyze_weekly_input_relation(
                    form_data, 
                    exemplar_content, 
                    exemplar_name
                )
                
                if not is_related:
                    return JsonResponse({
                        'success': False,
                        'error': f'INPUT VALIDATION ERROR: Your weekly lesson inputs are not sufficiently related to the selected exemplar "{exemplar_name}".\n\n'
                                f'Analysis: {explanation}\n\n'
                                f'Please either:\n'
                                f'1. Choose a different exemplar that matches your subject/topic\n'
                                f'2. Adjust your weekly lesson inputs\n'
                                f'3. Deselect the exemplar',
                        'validation_error': True,
                        'exemplar_name': exemplar_name,
                        'confidence_score': confidence,
                        'analysis_explanation': explanation
                    }, status=400)
                    
            except Exemplar.DoesNotExist:
                print("Selected exemplar not found")
            except Exception as e:
                print(f"Error loading exemplar: {str(e)}")
        
        # Format daily objectives for prompt
        daily_objectives_text = ""
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
            day_obj = objectives.get(day, '').strip()
            if day_obj:
                daily_objectives_text += f"{day.upper()}: {day_obj}\n"
            else:
                daily_objectives_text += f"{day.upper()}: [To be developed based on weekly theme]\n"
        
        # Format the prompt for the AI
        prompt = f"""
        Generate a complete MATATAG-aligned WEEKLY LESSON PLAN following DepEd Philippines standards.
        
        WEEKLY TITLE: {form_data['title'] or f"Week {form_data['week']}: {form_data['subject']}"}
        
        SUBJECT: {form_data['subject']}
        GRADE LEVEL: {form_data['grade_level']}
        WEEK NUMBER: {form_data['week']}
        QUARTER: {form_data['quarter']}
        
        WEEKLY THEME FOCUS: {form_data['theme'] or 'Comprehensive weekly progression'}
        TEACHING APPROACH: {form_data['approach'] or 'Varied instructional strategies'}
        INTELLIGENCE TYPE FOCUS: {form_data['intelligence_type']}
        
        CONTENT STANDARDS (Weekly):
        {form_data['content_standards'] or 'To be aligned with MATATAG curriculum'}
        
        PERFORMANCE STANDARDS (Weekly):
        {form_data['performance_standards'] or 'To be aligned with MATATAG curriculum'}
        
        DAILY LEARNING OBJECTIVES:
        {daily_objectives_text}

        {'REFERENCE EXEMPLAR: ' + exemplar_name if exemplar_name else ''}
        {'EXEMPLAR CONTENT FOR REFERENCE: ' + exemplar_content[:2000] + '...' if exemplar_content else ''}

        Generate a comprehensive weekly lesson plan following DepEd MATATAG format with:
        1. Complete school header (School, Teacher, Grade Level, Dates, Quarter)
        2. I. OBJECTIVES (Content Standards, Performance Standards, Learning Competencies/Objectives by day)
        3. II. CONTENT (Daily topics/themes)
        4. III. LEARNING RESOURCES (References, Materials, Textbook pages, LR Portal)
        5. IV. PROCEDURE (Complete MATATAG 10-step procedure for EACH DAY: A-J)
        6. V. REMARKS (Reflection section)
        7. VI. REFLECTION (For teacher's notes)
        
        Format each day's procedure with proper MATATAG structure:
        A. Reviewing previous lesson or presenting the new lesson
        B. Establishing a purpose for the lesson
        C. Presenting examples/instances of the new lesson
        D. Discussing new concepts and practicing new skills #1
        E. Discussing new concepts and practicing new skills #2
        F. Developing mastery (Leads to Formative Assessment)
        G. Finding practical applications of concepts and skills
        H. Making generalizations and abstractions about the lesson
        I. Evaluating learning
        J. Additional activities for application or remediation
        
        Ensure all content is MATATAG-aligned and appropriate for the grade level.
        """
        
        # Generate the lesson plan using Gemini
        try:
            has_exemplar = bool(form_data['exemplar_id'] and exemplar_content)
            
            # Use weekly-specific system instruction
            system_instruction = get_weekly_system_instruction(
                has_exemplar=has_exemplar,
                intelligence_type=form_data['intelligence_type']
            )
            
            response = model.generate_content([
                system_instruction,
                prompt
            ])
            
            print("Weekly AI response received")
            
            # Store in session
            request.session['generated_weekly_plan'] = response.text
            request.session['weekly_form_data'] = form_data
            request.session.modified = True
            
            return JsonResponse({
                'success': True,
                'weekly_plan': response.text,
                'exemplar_used': has_exemplar,
                'intelligence_type': form_data['intelligence_type'],
                'exemplar_id': form_data['exemplar_id'] if has_exemplar else None,
                'exemplar_name': exemplar_name if has_exemplar else None,
                'validation_passed': True if has_exemplar else None
            })
            
        except Exception as ai_error:
            print(f"Weekly AI error: {str(ai_error)}")
            return JsonResponse({
                'success': False,
                'error': f'AI service error: {str(ai_error)}'
            }, status=500)
        
    except Exception as e:
        print(f"Server error in weekly generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


def analyze_weekly_input_relation(user_inputs, exemplar_content, exemplar_name):
    """
    Analyze if weekly lesson inputs are related to the selected exemplar
    Same validation as daily lesson plans
    """
    try:
        if not exemplar_content or not user_inputs:
            return True, "No exemplar selected", 1.0
        
        # Get objectives
        objectives = user_inputs.get('objectives', {})
        objectives_text = ' '.join([
            objectives.get('monday', ''), 
            objectives.get('tuesday', ''),
            objectives.get('wednesday', ''),
            objectives.get('thursday', ''),
            objectives.get('friday', '')
        ])
        
        # Prepare analysis prompt
        analysis_prompt = f"""
        Analyze the relationship between the user's weekly lesson inputs and the selected exemplar.
        
        USER INPUTS:
        Subject: {user_inputs.get('subject', '')}
        Grade Level: {user_inputs.get('grade_level', '')}
        Week: {user_inputs.get('week', '')}
        Quarter: {user_inputs.get('quarter', '')}
        Content Standards: {user_inputs.get('content_standards', '')[:200]}
        Learning Objectives: {objectives_text[:300]}
        
        SELECTED EXEMPLAR: {exemplar_name}
        EXEMPLAR CONTENT (first 2000 chars): {exemplar_content[:2000]}
        
        ANALYSIS TASK:
        Determine if the weekly lesson inputs are related to the exemplar.
        Check for subject alignment, grade level appropriateness, and topic compatibility.
        
        Return ONLY a JSON object:
        {{
            "is_related": true/false,
            "confidence_score": 0.0-1.0,
            "explanation": "Detailed explanation",
            "specific_issues": ["Issues if unrelated"],
            "suggestions": ["Suggestions for alignment"]
        }}
        """
        
        response = model.generate_content([
            "You are an educational content analyst. Return only JSON.",
            analysis_prompt
        ])
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            analysis_result = json.loads(json_match.group())
            return (
                analysis_result.get('is_related', True),
                analysis_result.get('explanation', ''),
                analysis_result.get('confidence_score', 0.0)
            )
        else:
            return True, "Analysis failed, proceeding with caution", 0.5
            
    except Exception as e:
        print(f"Weekly relationship analysis error: {str(e)}")
        return True, f"Analysis error: {str(e)}", 0.5


def view_weekly_lesson_plan(request):
    """Render the weekly lesson plan result page"""
    weekly_plan = request.session.get('generated_weekly_plan', '')
    form_data = request.session.get('weekly_form_data', {})
    
    if not weekly_plan:
        messages.error(request, 'No weekly lesson plan found. Please generate one first.')
        return redirect('lesson_ai_weekly')
    
    # Process markdown
    import markdown
    weekly_plan_html = markdown.markdown(weekly_plan, extensions=['extra', 'nl2br', 'tables'])
    
    return render(request, 'lessonGenerator/view_weekly_lesson_plan.html', {
        'weekly_plan': weekly_plan_html,
        'form_data': form_data,
        'intelligence_type': form_data.get('intelligence_type', 'comprehensive')
    })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def save_weekly_lesson_plan(request):
    """
    Save the generated weekly lesson plan as a draft
    Must save before editing - appears in draft list with weekly indicator
    """
    try:
        # Get data from session
        generated_content = request.session.get('generated_weekly_plan', '')
        form_data = request.session.get('weekly_form_data', {})
        
        print(f"Session data - generated_content length: {len(generated_content) if generated_content else 0}")
        print(f"Session data - form_data: {form_data}")
        
        if not generated_content:
            return JsonResponse({
                'success': False,
                'error': 'No weekly lesson plan content found. Please generate one first.'
            }, status=400)
        
        # Check if user is department head for auto-approval
        is_department_head = hasattr(request.user, 'role') and request.user.role == 'Department Head'
        
        # Parse the generated content to extract structured data
        parsed_data = parse_weekly_lesson_plan(generated_content, form_data)
        
        # Create weekly lesson plan object
        weekly_plan = WeeklyLessonPlan(
            title=parsed_data.get('title', form_data.get('title', f"Week {form_data.get('week', '')} Lesson Plan")),
            subject=form_data.get('subject', ''),
            grade_level=form_data.get('grade_level', ''),
            quarter=form_data.get('quarter', ''),
            week_number=int(form_data.get('week', 0)) if str(form_data.get('week', '')).isdigit() else 0,
            
            # School info from parsed data
            school=parsed_data.get('school', ''),
            teacher=parsed_data.get('teacher', request.user.get_full_name() or request.user.username),
            teaching_date=parsed_data.get('teaching_date', ''),
            
            # Standards
            content_standard=parsed_data.get('content_standard', form_data.get('content_standards', '')),
            performance_standard=parsed_data.get('performance_standard', form_data.get('performance_standards', '')),
            
            # Daily objectives
            objective_monday=parsed_data.get('objective_monday', form_data.get('objectives', {}).get('monday', '')),
            objective_tuesday=parsed_data.get('objective_tuesday', form_data.get('objectives', {}).get('tuesday', '')),
            objective_wednesday=parsed_data.get('objective_wednesday', form_data.get('objectives', {}).get('wednesday', '')),
            objective_thursday=parsed_data.get('objective_thursday', form_data.get('objectives', {}).get('thursday', '')),
            objective_friday=parsed_data.get('objective_friday', form_data.get('objectives', {}).get('friday', '')),
            
            # Daily content
            content_monday=parsed_data.get('content_monday', ''),
            content_tuesday=parsed_data.get('content_tuesday', ''),
            content_wednesday=parsed_data.get('content_wednesday', ''),
            content_thursday=parsed_data.get('content_thursday', ''),
            content_friday=parsed_data.get('content_friday', ''),
            
            # Learning Resources
            teachers_guide=parsed_data.get('teachers_guide', ''),
            learning_materials=parsed_data.get('learning_materials', ''),
            textbook_pages=parsed_data.get('textbook_pages', ''),
            lr_portal=parsed_data.get('lr_portal', ''),
            other_resources=parsed_data.get('other_resources', ''),
            
            # Generated content
            generated_content=generated_content,
            
            # Metadata
            weekly_theme=form_data.get('theme', ''),
            teaching_approach=form_data.get('approach', ''),
            intelligence_type=form_data.get('intelligence_type', 'comprehensive'),
            
            # Status
            status=WeeklyLessonPlan.FINAL if is_department_head else WeeklyLessonPlan.DRAFT,
            auto_approved=is_department_head,
            created_by=request.user,
        )
        
        # Set all procedure fields from parsed_data
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        steps = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
        
        for day in days:
            for step in steps:
                field_name = f'{day}_procedure_{step}'
                setattr(weekly_plan, field_name, parsed_data.get(field_name, ''))
        
        # Set exemplar if used
        if form_data.get('exemplar_id'):
            try:
                from lesson.models import Exemplar
                weekly_plan.exemplar_used = Exemplar.objects.get(id=form_data['exemplar_id'])
            except:
                pass
        
        weekly_plan.save()
        print(f"Weekly lesson plan saved with ID: {weekly_plan.id}")
        
        # Clear session data
        if 'generated_weekly_plan' in request.session:
            del request.session['generated_weekly_plan']
        if 'weekly_form_data' in request.session:
            del request.session['weekly_form_data']
        
        message = 'Weekly lesson plan saved as draft successfully!'
        if is_department_head:
            message = 'Weekly lesson plan created and automatically approved!'
        
        return JsonResponse({
            'success': True,
            'draft_id': weekly_plan.id,
            'message': message,
            'intelligence_type': form_data.get('intelligence_type', 'comprehensive'),
            'auto_approved': is_department_head,
            'redirect_url': '/drafts/weekly/'
        })
        
    except Exception as e:
        import traceback
        print(f"Error saving weekly lesson plan: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Error saving weekly lesson plan: {str(e)}'
        }, status=500)


def parse_weekly_lesson_plan(content, form_data):
    """
    Parse AI-generated weekly lesson plan into structured fields
    """
    parsed = {
        'title': form_data.get('title', ''),
        'school': '',
        'teacher': '',
        'teaching_date': '',
        'content_standard': '',
        'performance_standard': '',
        'objective_monday': '',
        'objective_tuesday': '',
        'objective_wednesday': '',
        'objective_thursday': '',
        'objective_friday': '',
        'content_monday': '',
        'content_tuesday': '',
        'content_wednesday': '',
        'content_thursday': '',
        'content_friday': '',
        'teachers_guide': '',
        'learning_materials': '',
        'textbook_pages': '',
        'lr_portal': '',
        'other_resources': '',
        'melc_codes': '',
        'values_integration': '',
        'cross_curricular': '',
    }
    
    # Initialize procedure fields for all days
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    steps = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
    
    for day in days:
        for step in steps:
            parsed[f'{day}_procedure_{step}'] = ''
    
    # Parse school header
    school_match = re.search(r'School[:\s]+([^\n]+)', content, re.IGNORECASE)
    if school_match:
        parsed['school'] = school_match.group(1).strip()
    
    teacher_match = re.search(r'Teacher[:\s]+([^\n]+)', content, re.IGNORECASE)
    if teacher_match:
        parsed['teacher'] = teacher_match.group(1).strip()
    
    date_match = re.search(r'Teaching Date and Time[:\s]+([^\n]+)', content, re.IGNORECASE)
    if date_match:
        parsed['teaching_date'] = date_match.group(1).strip()
    
    # Parse I. OBJECTIVES section
    objectives_section = extract_section(content, r'I\.?\s*OBJECTIVES', r'II\.?\s*CONTENT')
    
    if objectives_section:
        # Content Standards
        cs_match = re.search(r'Content Standards?[:\s]+(.*?)(?=Performance Standards?|$)', objectives_section, re.DOTALL | re.IGNORECASE)
        if cs_match:
            parsed['content_standard'] = cs_match.group(1).strip()
        
        # Performance Standards
        ps_match = re.search(r'Performance Standards?[:\s]+(.*?)(?=Learning Competencies?|Learning Objectives?|$)', objectives_section, re.DOTALL | re.IGNORECASE)
        if ps_match:
            parsed['performance_standard'] = ps_match.group(1).strip()
        
        # Daily objectives
        for day in days:
            day_pattern = rf'{day.capitalize()}[:\s]+(.*?)(?={day.capitalize()}|Tuesday|Wednesday|Thursday|Friday|$|\[|\(|\))'
            day_match = re.search(day_pattern, objectives_section, re.DOTALL | re.IGNORECASE)
            if day_match:
                parsed[f'objective_{day}'] = day_match.group(1).strip()
    
    # Parse II. CONTENT section
    content_section = extract_section(content, r'II\.?\s*CONTENT', r'III\.?\s*LEARNING RESOURCES')
    
    if content_section:
        for day in days:
            day_pattern = rf'{day.capitalize()}[:\s]+(.*?)(?={day.capitalize()}|Tuesday|Wednesday|Thursday|Friday|$|\[|\(|\))'
            day_match = re.search(day_pattern, content_section, re.DOTALL | re.IGNORECASE)
            if day_match:
                parsed[f'content_{day}'] = day_match.group(1).strip()
    
    # Parse III. LEARNING RESOURCES
    resources_section = extract_section(content, r'III\.?\s*LEARNING RESOURCES', r'IV\.?\s*PROCEDURE')
    
    if resources_section:
        tg_match = re.search(r'Teacher\'?s Guide[:\s]+([^\n]+)', resources_section, re.IGNORECASE)
        if tg_match:
            parsed['teachers_guide'] = tg_match.group(1).strip()
        
        lm_match = re.search(r'Learning Materials?[:\s]+([^\n]+)', resources_section, re.IGNORECASE)
        if lm_match:
            parsed['learning_materials'] = lm_match.group(1).strip()
        
        tb_match = re.search(r'Textbook Pages?[:\s]+([^\n]+)', resources_section, re.IGNORECASE)
        if tb_match:
            parsed['textbook_pages'] = tb_match.group(1).strip()
        
        lr_match = re.search(r'LR Portal[:\s]+([^\n]+)', resources_section, re.IGNORECASE)
        if lr_match:
            parsed['lr_portal'] = lr_match.group(1).strip()
        
        other_match = re.search(r'Other Learning Resources?[:\s]+(.*?)(?=IV|$)', resources_section, re.DOTALL | re.IGNORECASE)
        if other_match:
            parsed['other_resources'] = other_match.group(1).strip()
    
    # Parse IV. PROCEDURE for each day
    procedure_section = extract_section(content, r'IV\.?\s*PROCEDURE', r'V\.?\s*REMARKS')
    
    if procedure_section:
        for day in days:
            # Find this day's subsection
            day_pattern = rf'{day.capitalize()}\s*(.*?)(?={day.capitalize()}|Tuesday|Wednesday|Thursday|Friday|V\.|$|\[|\(|\))'
            day_match = re.search(day_pattern, procedure_section, re.DOTALL | re.IGNORECASE)
            
            if day_match:
                day_content = day_match.group(1)
                
                # Extract each step A-J
                for step in steps:
                    step_upper = step.upper()
                    step_pattern = rf'{step_upper}\.?[\)\.]?\s*(.*?)(?={step_upper}|[A-J]\.|$|\[|\(|\))'
                    step_match = re.search(step_pattern, day_content, re.DOTALL | re.IGNORECASE)
                    if step_match:
                        parsed[f'{day}_procedure_{step}'] = step_match.group(1).strip()
    
    return parsed


def extract_section(content, start_pattern, end_pattern):
    """Extract a section between two patterns"""
    start_match = re.search(start_pattern, content, re.IGNORECASE)
    if not start_match:
        return ""
    
    start_pos = start_match.end()
    
    end_match = re.search(end_pattern, content[start_pos:], re.IGNORECASE)
    if end_match:
        end_pos = start_pos + end_match.start()
        return content[start_pos:end_pos].strip()
    else:
        return content[start_pos:].strip()


@login_required
def weekly_draft_list(request):
    """Display list of weekly lesson plan drafts"""
    # Get all weekly drafts for the user
    drafts = WeeklyLessonPlan.objects.filter(
        created_by=request.user
    ).order_by('-created_at')
    
    # Get submission status for each draft
    draft_data = []
    for draft in drafts:
        draft_data.append({
            'draft': draft,
            'latest_submission': draft.get_latest_submission()
        })
    
    # Count by status
    draft_count = drafts.filter(status=WeeklyLessonPlan.DRAFT).count()
    final_count = drafts.filter(status=WeeklyLessonPlan.FINAL).count()
    
    return render(request, 'lessonGenerator/weekly_draft_list.html', {
        'draft_data': draft_data,
        'draft_count': draft_count,
        'final_count': final_count,
        'is_weekly': True
    })


@login_required
def view_weekly_draft(request, draft_id):
    """View a weekly lesson draft in read-only format with template"""
    draft = get_object_or_404(WeeklyLessonPlan, id=draft_id, created_by=request.user)
    
    # Get submission status if exists
    latest_submission = draft.get_latest_submission()
    
    # Get intelligence type display
    intelligence_display = dict(WeeklyLessonPlan.INTELLIGENCE_TYPE_CHOICES).get(
        draft.intelligence_type, 
        draft.intelligence_type
    )
    
    # Get daily procedures
    procedures = {}
    for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
        procedures[day] = draft.get_procedure_for_day(day)
    
    return render(request, 'lessonGenerator/view_weekly_draft.html', {
        'draft': draft,
        'procedures': procedures,
        'latest_submission': latest_submission,
        'intelligence_display': intelligence_display,
        'objectives': draft.get_objectives_dict(),
        'content': draft.get_content_dict(),
    })


@login_required
def edit_weekly_draft(request, draft_id):
    """Edit a saved weekly draft"""
    draft = get_object_or_404(WeeklyLessonPlan, id=draft_id, created_by=request.user)
    
    if request.method == 'POST':
        # Update basic info
        draft.title = request.POST.get('title', draft.title)
        draft.subject = request.POST.get('subject', draft.subject)
        draft.grade_level = request.POST.get('grade_level', draft.grade_level)
        draft.quarter = request.POST.get('quarter', draft.quarter)
        draft.week_number = int(request.POST.get('week_number', draft.week_number))
        
        # Update school info
        draft.school = request.POST.get('school', draft.school)
        draft.teacher = request.POST.get('teacher', draft.teacher)
        draft.teaching_date = request.POST.get('teaching_date', draft.teaching_date)
        
        # Update standards
        draft.content_standard = request.POST.get('content_standard', draft.content_standard)
        draft.performance_standard = request.POST.get('performance_standard', draft.performance_standard)
        
        # Update daily objectives
        draft.objective_monday = request.POST.get('objective_monday', draft.objective_monday)
        draft.objective_tuesday = request.POST.get('objective_tuesday', draft.objective_tuesday)
        draft.objective_wednesday = request.POST.get('objective_wednesday', draft.objective_wednesday)
        draft.objective_thursday = request.POST.get('objective_thursday', draft.objective_thursday)
        draft.objective_friday = request.POST.get('objective_friday', draft.objective_friday)
        
        # Update daily content
        draft.content_monday = request.POST.get('content_monday', draft.content_monday)
        draft.content_tuesday = request.POST.get('content_tuesday', draft.content_tuesday)
        draft.content_wednesday = request.POST.get('content_wednesday', draft.content_wednesday)
        draft.content_thursday = request.POST.get('content_thursday', draft.content_thursday)
        draft.content_friday = request.POST.get('content_friday', draft.content_friday)
        
        # Update resources
        draft.teachers_guide = request.POST.get('teachers_guide', draft.teachers_guide)
        draft.learning_materials = request.POST.get('learning_materials', draft.learning_materials)
        draft.textbook_pages = request.POST.get('textbook_pages', draft.textbook_pages)
        draft.lr_portal = request.POST.get('lr_portal', draft.lr_portal)
        draft.other_resources = request.POST.get('other_resources', draft.other_resources)
        
        # Update all procedures - Monday
        for step in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']:
            # Monday
            field_name = f'monday_procedure_{step}'
            setattr(draft, field_name, request.POST.get(field_name, getattr(draft, field_name)))
            
            # Tuesday
            field_name = f'tuesday_procedure_{step}'
            setattr(draft, field_name, request.POST.get(field_name, getattr(draft, field_name)))
            
            # Wednesday
            field_name = f'wednesday_procedure_{step}'
            setattr(draft, field_name, request.POST.get(field_name, getattr(draft, field_name)))
            
            # Thursday
            field_name = f'thursday_procedure_{step}'
            setattr(draft, field_name, request.POST.get(field_name, getattr(draft, field_name)))
            
            # Friday
            field_name = f'friday_procedure_{step}'
            setattr(draft, field_name, request.POST.get(field_name, getattr(draft, field_name)))
        
        # Update metadata
        draft.intelligence_type = request.POST.get('intelligence_type', draft.intelligence_type)
        draft.weekly_theme = request.POST.get('weekly_theme', draft.weekly_theme)
        draft.teaching_approach = request.POST.get('teaching_approach', draft.teaching_approach)
        draft.melc_codes = request.POST.get('melc_codes', draft.melc_codes)
        draft.values_integration = request.POST.get('values_integration', draft.values_integration)
        draft.cross_curricular = request.POST.get('cross_curricular', draft.cross_curricular)
        
        draft.save()
        
        messages.success(request, 'Weekly draft updated successfully!')
        return redirect('weekly_draft_list')
    
    # Prepare data for template
    procedures = {}
    for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
        procedures[day] = draft.get_procedure_for_day(day)
    
    return render(request, 'lessonGenerator/edit_weekly_draft.html', {
        'draft': draft,
        'procedures': procedures,
        'objectives': draft.get_objectives_dict(),
        'content': draft.get_content_dict(),
        'intelligence_choices': WeeklyLessonPlan.INTELLIGENCE_TYPE_CHOICES,
        'theme_choices': WeeklyLessonPlan.WEEK_DAYS,
        'approach_choices': [
            ('direct', 'Direct Instruction'),
            ('collaborative', 'Collaborative Learning'),
            ('hands_on', 'Hands-on/Practical'),
            ('inquiry', 'Inquiry-Based'),
        ],
    })


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def delete_weekly_draft(request, draft_id):
    """Delete a weekly lesson draft"""
    try:
        draft = get_object_or_404(WeeklyLessonPlan, id=draft_id, created_by=request.user)
        draft.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Weekly lesson plan deleted successfully!'
        })
        
    except WeeklyLessonPlan.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Weekly lesson plan not found.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error deleting: {str(e)}'
        }, status=500)


@login_required
def submit_weekly_plan(request, draft_id):
    """Submit weekly plan to department head for review"""
    if request.method != 'POST':
        return redirect('view_weekly_draft', draft_id=draft_id)
    
    draft = get_object_or_404(WeeklyLessonPlan, id=draft_id, created_by=request.user)
    
    # Check if department head exists
    if not hasattr(request.user, 'department') or not request.user.department:
        messages.error(request, "You don't have a department assigned. Please contact your administrator.")
        return redirect('view_weekly_draft', draft_id=draft_id)
    
    # Find department head
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    department_head = User.objects.filter(
        role='Department Head',
        department=request.user.department,
        school=request.user.school
    ).first()
    
    if not department_head:
        messages.error(request, "No department head found for your department.")
        return redirect('view_weekly_draft', draft_id=draft_id)
    
    # Submit
    success, message = draft.submit_for_approval(department_head)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return redirect('view_weekly_draft', draft_id=draft_id)