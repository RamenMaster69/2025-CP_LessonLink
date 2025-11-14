# views.py
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
from .ai_instructions import LESSON_PLANNER_SYSTEM_INSTRUCTION, EXEMPLAR_REFERENCE_INSTRUCTION

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
        
        # Extract form data with validation - MATCHING THE ACTUAL FORM FIELDS
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
            'selected_exemplar': data.get('selected_exemplar', '').strip(),  # Add exemplar reference
        }
        
        print("Form data prepared:", form_data)  # Debugging
        
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
            except Exemplar.DoesNotExist:
                print("Selected exemplar not found")
            except Exception as e:
                print(f"Error loading exemplar: {str(e)}")
        
        # Format the prompt for the AI - MATCHING THE FORM STRUCTURE
        prompt = f"""
        Create a comprehensive MELC-aligned lesson plan based on these details:

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
        {'EXEMPLAR CONTENT FOR REFERENCE: ' + exemplar_content if exemplar_content else ''}

        Generate this as a complete MELC-aligned lesson plan following DepEd Philippines standards.
        Use the learning objectives provided to create specific, measurable outcomes.
        {'Use the reference exemplar as a guide for structure, depth, and quality standards while maintaining originality.' if exemplar_content else ''}
        """
        
        print("Sending prompt to AI")  # Debugging
        print(f"Exemplar provided: {bool(exemplar_content)}")  # Debugging
        
        # Generate the lesson plan using Gemini
        try:
            # Check if exemplar is provided
            has_exemplar = bool(form_data['selected_exemplar'] and exemplar_content)
            
            # Use appropriate system instruction
            if has_exemplar:
                system_instruction = LESSON_PLANNER_SYSTEM_INSTRUCTION + "\n\n" + EXEMPLAR_REFERENCE_INSTRUCTION
                print("Using enhanced system instruction with exemplar guidance")  # Debugging
            else:
                system_instruction = LESSON_PLANNER_SYSTEM_INSTRUCTION
                print("Using standard system instruction")  # Debugging
            
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
                        'exemplar_id': form_data['selected_exemplar'] if has_exemplar else None,
                        'exemplar_name': exemplar_name if has_exemplar else None
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
                        'exemplar_id': form_data['selected_exemplar'] if has_exemplar else None,
                        'exemplar_name': exemplar_name if has_exemplar else None
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
                    'exemplar_id': form_data['selected_exemplar'] if has_exemplar else None,
                    'exemplar_name': exemplar_name if has_exemplar else None
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
    
    if not lesson_plan:
        messages.error(request, 'No lesson plan found. Please generate a lesson plan first.')
        return redirect('lesson_ai')
    
    # Process markdown in the view
    import markdown
    lesson_plan_html = markdown.markdown(lesson_plan, extensions=['extra', 'nl2br'])
    
    return render(request, 'lessonGenerator/lesson_plan.html', {
        'lesson_plan': lesson_plan_html
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
        'rejected_count': rejected_count
    })

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
        
        # Format the prompt for the AI with MELC focus
        prompt = f"""
        Create a comprehensive MELC-aligned lesson plan based on these details:

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
        Include appropriate MELC codes, content standards, performance standards, and learning competencies.
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

@login_required
def view_draft(request, draft_id):
    """View a lesson draft in read-only format"""
    draft = get_object_or_404(LessonPlan, id=draft_id, created_by=request.user)
    
    # Get submission status if exists
    latest_submission = LessonPlanSubmission.objects.filter(
        lesson_plan=draft
    ).order_by('-submission_date').first()
    
    return render(request, 'lessonGenerator/view_draft.html', {
        'draft': draft,
        'latest_submission': latest_submission
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
    
    return render(request, 'lessonGenerator/department_head_drafts.html', {
        'approved_plans': approved_plans,
        'draft_plans': draft_plans,
        'approved_count': approved_plans.count(),
        'draft_count': draft_plans.count(),
        'is_department_head': True
    })

@csrf_exempt
@require_http_methods(["POST"])
def get_ai_suggestions(request):
    """Generate AI suggestions for specific lesson plan sections"""
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
        
        # Create context-aware prompt for suggestions with MELC focus
        prompt = f"""
        Analyze this lesson plan context and provide 3 targeted MELC-aligned suggestions for the {section} section.
        
        CONTEXT:
        Subject: {form_data.get('subject', 'Not specified')}
        Grade Level: {form_data.get('gradeLevel', 'Not specified')}
        Learning Objectives: {form_data.get('learningObjectives', 'Not specified')}
        Subject Matter: {form_data.get('subjectMatter', 'Not specified')}
        
        Provide 3 specific, actionable MELC-aligned suggestions for the {section} section that are appropriate for this context.
        Focus on DepEd Philippines standards and curriculum alignment.
        Return ONLY a JSON array with this exact format:
        [
            {{
                "title": "MELC-aligned suggestion title",
                "description": "Detailed suggestion description with MELC focus",
                "example": "Concrete example or implementation idea aligned with DepEd standards"
            }}
        ]
        """
        
        response = model.generate_content([
            "You are an expert educational consultant specialized in DepEd Philippines curriculum. Provide specific, practical MELC-aligned suggestions for lesson plan sections.",
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
                "title": "MELC-Aligned Suggestion",
                "description": response.text[:200] + "...",
                "example": "Based on DepEd curriculum standards"
            }]
        
        return JsonResponse({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        print(f"AI suggestions error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Suggestion generation failed: {str(e)}'
        }, status=500)