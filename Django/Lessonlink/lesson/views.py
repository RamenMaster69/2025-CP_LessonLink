# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage 
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.views.decorators.http import require_POST
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.utils import timezone
import json
import os
import time
import logging
from PIL import Image
import uuid
from io import BytesIO

from .models import User, Schedule, Task, TaskNotification, SchoolRegistration
from .serializers import ScheduleSerializer

logger = logging.getLogger(__name__)

# School Registration Views

def org_reg_1(request):
    """Handle school registration form - both GET and POST"""
    
    if request.method == 'GET':
        # Display the form
        return render(request, 'org_reg/org_reg_1.html')
    
    elif request.method == 'POST':
        try:
            # Extract form data
            form_data = {
                'school_name': request.POST.get('school_name', '').strip(),
                'school_id': request.POST.get('school_id', '').strip(),
                'year_established': request.POST.get('year_established'),
                'address': request.POST.get('address', '').strip(),
                'province': request.POST.get('province', '').strip(),
                'region': request.POST.get('region', '').strip(),
                'phone_number': request.POST.get('phone_number', '').strip(),
                'email': request.POST.get('email', '').strip(),
                'website': request.POST.get('website', '').strip(),
                'facebook_page': request.POST.get('facebook_page', '').strip(),
                'contact_person': request.POST.get('contact_person', '').strip(),
                'position': request.POST.get('position', '').strip(),
                'contact_email': request.POST.get('contact_email', '').strip(),
                'contact_phone': request.POST.get('contact_phone', '').strip(),
                'accuracy': request.POST.get('accuracy') == 'on',
                'terms': request.POST.get('terms') == 'on',
                'communications': request.POST.get('communications') == 'on',
            }
            
            # Handle year_established - convert to int if provided
            if form_data['year_established']:
                try:
                    form_data['year_established'] = int(form_data['year_established'])
                except (ValueError, TypeError):
                    form_data['year_established'] = None
            else:
                form_data['year_established'] = None
            
            # Validate required fields
            required_fields = [
                'school_name', 'school_id', 'address', 'province', 'region',
                'phone_number', 'email', 'contact_person', 'position',
                'contact_email', 'contact_phone'
            ]
            
            missing_fields = []
            for field in required_fields:
                if not form_data[field]:
                    missing_fields.append(field.replace('_', ' ').title())
            
            if missing_fields:
                messages.error(request, f"Please complete the following required fields: {', '.join(missing_fields)}")
                return render(request, 'org_reg/org_reg_1.html', {'form_data': form_data})
            
            # Validate required checkboxes
            if not form_data['accuracy']:
                messages.error(request, "You must certify the accuracy of the information provided.")
                return render(request, 'org_reg/org_reg_1.html', {'form_data': form_data})
            
            if not form_data['terms']:
                messages.error(request, "You must agree to the Terms of Service and Privacy Policy.")
                return render(request, 'org_reg/org_reg_1.html', {'form_data': form_data})
            
            # Check if school_id already exists
            if SchoolRegistration.objects.filter(school_id=form_data['school_id']).exists():
                messages.error(request, f"A school with ID '{form_data['school_id']}' is already registered.")
                return render(request, 'org_reg/org_reg_1.html', {'form_data': form_data})
            
            # Create the school registration record
            school_registration = SchoolRegistration.objects.create(
                school_name=form_data['school_name'],
                school_id=form_data['school_id'],
                year_established=form_data['year_established'],
                address=form_data['address'],
                province=form_data['province'],
                region=form_data['region'],
                phone_number=form_data['phone_number'],
                email=form_data['email'],
                website=form_data['website'] if form_data['website'] else None,
                facebook_page=form_data['facebook_page'] if form_data['facebook_page'] else None,
                contact_person=form_data['contact_person'],
                position=form_data['position'],
                contact_email=form_data['contact_email'],
                contact_phone=form_data['contact_phone'],
                accuracy=form_data['accuracy'],
                terms=form_data['terms'],
                communications=form_data['communications'],
                status='pending'
            )
            
            # Handle file upload if present
            # if request.FILES.get('certificate_file'):
            #     school_registration.certificate_file = request.FILES['certificate_file']
            #     school_registration.save()
            
            # Log the successful registration
            logger.info(f"New school registration: {school_registration.school_name} ({school_registration.school_id})")
            
            # Success message
            messages.success(
                request, 
                f"Registration submitted successfully! "
                f"Your application for {school_registration.school_name} has been received. "
                f"You will be contacted at {school_registration.contact_email} once your registration is reviewed."
            )
            
            # Create success context
            context = {
                'school_registration': school_registration,
                'success': True
            }
            
            return redirect('landing')
            
        except ValidationError as e:
            # Handle model validation errors
            error_messages = []
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        error_messages.append(f"{field.replace('_', ' ').title()}: {error}")
            else:
                error_messages.append(str(e))
            
            for error in error_messages:
                messages.error(request, error)
            
            return render(request, 'org_reg/org_reg_1.html', {'form_data': request.POST})
        
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Error processing school registration: {str(e)}")
            messages.error(request, "An unexpected error occurred. Please try again or contact support.")
            return render(request, 'org_reg/org_reg_1.html', {'form_data': request.POST})


# AJAX endpoint for real-time school ID validation
def validate_school_id_ajax(request):
    """AJAX endpoint to validate school ID availability"""
    school_id = request.POST.get('school_id', '').strip()
    
    if not school_id:
        return JsonResponse({'valid': False, 'message': 'School ID is required'})
    
    exists = SchoolRegistration.objects.filter(school_id=school_id).exists()
    
    if exists:
        return JsonResponse({
            'valid': False, 
            'message': 'This School ID is already registered'
        })
    
    return JsonResponse({
        'valid': True, 
        'message': 'School ID is available'
    })


# User Registration and Authentication Views
@login_required
def upload_profile_picture(request):
    if request.method == 'POST' and request.FILES.get('profile_picture'):
        profile_picture = request.FILES['profile_picture']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
        if profile_picture.content_type not in allowed_types:
            return JsonResponse({
                'success': False, 
                'message': 'Invalid file type. Please upload JPG, PNG, or GIF.'
            })
        
        # Validate file size (max 5MB)
        if profile_picture.size > 5 * 1024 * 1024:
            return JsonResponse({
                'success': False, 
                'message': 'File too large. Please upload an image smaller than 5MB.'
            })
        
        try:
            user = request.user
            
            # Delete old profile picture if exists
            if user.profile_picture:
                try:
                    if default_storage.exists(user.profile_picture.name):
                        default_storage.delete(user.profile_picture.name)
                except:
                    pass  # Continue even if deletion fails
            
            # Process and resize image using PIL
            image = Image.open(profile_picture)
            
            # Convert to RGB if necessary (for PNG with transparency)
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Resize image to max 500x500 while maintaining aspect ratio
            max_size = (500, 500)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Generate unique filename
            file_extension = profile_picture.name.split('.')[-1].lower()
            filename = f"profile_pictures/user_{user.id}_{uuid.uuid4().hex}.{file_extension}"
            
            # Save processed image to BytesIO
            output = BytesIO()
            image.save(output, format='JPEG', quality=90, optimize=True)
            output.seek(0)
            
            # Save to storage
            path = default_storage.save(filename, ContentFile(output.read()))
            
            # Update user's profile picture
            user.profile_picture = path
            user.save()
            
            # Return the URL for the image
            image_url = default_storage.url(path)
            return JsonResponse({
                'success': True, 
                'image_url': image_url,
                'message': 'Profile picture uploaded successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'message': f'Error processing image: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def landing(request):
    return render(request, 'landing.html')

@csrf_exempt
def registration_1(request):
    if request.method == 'POST':
        # Check if this is an AJAX request for email validation
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            email = request.POST.get('email')
            if email:
                exists = User.objects.filter(email=email).exists()
                if exists:
                    return JsonResponse({
                        'exists': True, 
                        'message': 'This email already has an account. Please use a different email or try logging in.'
                    })
                else:
                    return JsonResponse({
                        'exists': False, 
                        'message': 'Email is available.'
                    })
            return JsonResponse({
                'exists': False, 
                'message': 'Please enter a valid email.'
            })
        
        # Handle regular form submission
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')

        # Validation for empty fields
        if not email or not password or not confirm_password:
            messages.error(request, "Please fill in all fields.")
            return render(request, 'registration_1.html', {
                'email': email,
                'error_message': "Please fill in all fields.",
                'show_error': True
            })

        # Password confirmation validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'registration_1.html', {
                'email': email,
                'error_message': "Passwords do not match.",
                'password_mismatch': True,
                'show_error': True
            })

        # Email existence validation
        if User.objects.filter(email=email).exists():
            messages.error(request, "This email already has an account. Please use a different email or try logging in.")
            return render(request, 'registration_1.html', {
                'email': email,
                'email_exists': True,
                'error_message': "This email already has an account. Please use a different email or try logging in.",
                'show_error': True
            })

        # If all validations pass, store in session and proceed
        request.session['reg_email'] = email
        request.session['reg_password'] = password
        messages.success(request, "Email validated successfully!")
        return redirect('registration_2')

    # GET request - render empty form
    return render(request, 'registration/registration_1.html')

def registration_2(request):
    # Check if user came from registration_1
    if not request.session.get('reg_email'):
        messages.error(request, "Please start registration from the beginning.")
        return redirect('registration_1')
    
    if request.method == 'POST':
        first_name = request.POST.get('firstName')
        middle_name = request.POST.get('middleName', '')  # Optional field
        last_name = request.POST.get('lastName')
        dob = request.POST.get('dateOfBirth')

        if not first_name or not last_name or not dob:
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'registration_2.html', {
                'first_name': first_name,
                'middle_name': middle_name,
                'last_name': last_name,
                'dob': dob,
                'error_message': "Please fill in all required fields.",
                'show_error': True
            })

        # Store in session
        request.session['reg_first_name'] = first_name
        request.session['reg_middle_name'] = middle_name
        request.session['reg_last_name'] = last_name
        request.session['reg_dob'] = dob

        messages.success(request, "Personal information saved successfully!")
        return redirect('registration_3')

    return render(request, 'registration/registration_2.html')

def registration_3(request):
    # Debug: Show current session state
    print(f"DEBUG - Session at start: {dict(request.session)}")
    print(f"DEBUG - Has reg_email: {request.session.get('reg_email')}")
    print(f"DEBUG - Has reg_first_name: {request.session.get('reg_first_name')}")
    
    # Check if user came from previous steps
    if not request.session.get('reg_email') or not request.session.get('reg_first_name'):
        messages.error(request, "Please complete the previous registration steps.")
        return redirect('registration_1')
    
    if request.method == 'POST':
        role = request.POST.get('role')
        rank = request.POST.get('rank')
        
        print(f"DEBUG - POST data - role: {role}, rank: {rank}")

        if not role or not rank:
            messages.error(request, "Please select both role and rank.")
            return render(request, 'registration/registration_3.html', {
                'role': role,
                'rank': rank,
                'error_message': "Please select both role and rank.",
                'show_error': True
            })

        # Store in session
        request.session['reg_role'] = role
        request.session['reg_rank'] = rank
        request.session.modified = True
        
        # Debug: Verify session was set
        print(f"DEBUG - Session after setting: {dict(request.session)}")
        print(f"DEBUG - reg_role set to: {request.session.get('reg_role')}")

        messages.success(request, "Role and rank selected successfully!")
        return redirect('registration_4')

    return render(request, 'registration/registration_3.html')

def registration_4(request):
    # Debug logs
    print(f"DEBUG registration_4 - Full session: {dict(request.session)}")
    
    # Ensure previous steps are complete
    if not request.session.get('reg_email') or not request.session.get('reg_role'):
        messages.error(request, "Please complete the previous registration steps.")
        return redirect('registration_1')

    # Get approved schools for the dropdown
    approved_schools = SchoolRegistration.objects.filter(status='approved').order_by('school_name')

    if not approved_schools.exists():
        messages.warning(request, "No schools have been approved yet. Please contact an administrator.")
    
    # Debug info - check if we're getting any schools
    print(f"DEBUG - Approved schools count: {approved_schools.count()}")
    for school in approved_schools:
        print(f"DEBUG - School: {school.school_name} (ID: {school.id})")

    if request.method == "POST":
        department = request.POST.get("department")
        school_id = request.POST.get("school")  # Get selected school ID
        affiliations = request.POST.getlist("affiliation[]")
        
        # Get the school object
        try:
            school = SchoolRegistration.objects.get(id=school_id)
            school_name = school.school_name
        except (SchoolRegistration.DoesNotExist, ValueError):
            school_name = ""
            messages.error(request, "Please select a valid school.")

        # Validation for required fields
        if not department or not school_name:
            messages.error(request, "Please complete all required fields.")
            return render(request, 'registration/registration_4.html', {
                'department': department,
                'school': school_id,
                'affiliations': affiliations,
                'schools': approved_schools,
                'error_message': "Please complete all required fields.",
                'show_error': True
            })

        # Collect session data
        email = request.session.get('reg_email')
        raw_password = request.session.get('reg_password')
        first_name = request.session.get('reg_first_name')
        middle_name = request.session.get('reg_middle_name', '')
        last_name = request.session.get('reg_last_name')
        dob = request.session.get('reg_dob')
        role = request.session.get('reg_role')
        rank = request.session.get('reg_rank')

        # Check integrity
        if not email or not raw_password:
            messages.error(request, "Session expired. Please restart registration.")
            for key in list(request.session.keys()):
                if key.startswith("reg_"):
                    del request.session[key]
            return redirect('registration_1')

        try:
            # Prevent duplicate registration
            if User.objects.filter(email=email).exists():
                messages.error(request, "This email was registered by someone else. Please use a different email.")
                for key in list(request.session.keys()):
                    if key.startswith("reg_"):
                        del request.session[key]
                return redirect('registration_1')

            # Create user with Django's built-in User model
            user = User.objects.create_user(
                email=email,
                password=raw_password,  # Django handles hashing automatically
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                dob=dob,
                role=role,
                rank=rank,
                department=department,
                school=school,  # Store the school name
                affiliations=", ".join(affiliations) if affiliations else ""
            )

            # Clear reg_* session data
            for key in list(request.session.keys()):
                if key.startswith("reg_"):
                    del request.session[key]

            # Auto-login new user using Django's login function
            login(request, user)
            messages.success(request, f"Account created successfully for {email}!")

            # Redirect by role
            if user.role == "Student Teacher":
                return redirect('st_dash')
            elif user.role == "Department Head":
                return redirect('Dep_Dash')
            else:
                return redirect('dashboard')

        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return render(request, 'registration/registration_4.html', {
                'department': department,
                'school': school_id,
                'affiliations': affiliations,
                'schools': approved_schools,
                'error_message': f"Registration failed: {str(e)}",
                'show_error': True
            })

    # Handle GET request: just render the form
    return render(request, 'registration/registration_4.html', {
        'schools': approved_schools
    })
    
def registration_5(request):
    return render(request, 'registration/registration_5.html')

def login_view(request):
    # If user is already logged in, redirect based on role
    if request.user.is_authenticated:
        if request.user.role == "Student Teacher":
            return redirect('st_dash')
        elif request.user.role == "Department Head":
            return redirect('Dep_Dash')
        else:
            return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Validation for empty fields
        if not email or not password:
            messages.error(request, "Please fill in both email and password.")
            return render(request, 'login.html', {
                'email': email,
                'error_message': "Please fill in both email and password.",
                'show_error': True
            })

        # Use Django's built-in authenticate function
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            # User authentication successful
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name}!")

            # Redirect based on role
            if user.role == "Student Teacher":
                return redirect('st_dash')
            elif user.role == "Department Head":
                return redirect('Dep_Dash')
            else:
                return redirect('dashboard')
        else:
            # Check if user exists to give specific error message
            try:
                existing_user = User.objects.get(email=email)
                messages.error(request, "Invalid password. Please try again.")
                return render(request, 'login.html', {
                    'email': email,
                    'error_message': "Invalid password. Please try again.",
                    'invalid_password': True,
                    'show_error': True
                })
            except User.DoesNotExist:
                messages.error(request, "No account found with this email. Please register first.")
                return render(request, 'login.html', {
                    'email': email,
                    'error_message': "No account found with this email. Please register first.",
                    'email_not_found': True,
                    'show_error': True
                })

    return render(request, 'login.html')

@login_required
def dashboard(request):
    user = request.user
    
    # Get task statistics for dashboard
    total_tasks = Task.objects.filter(user=user).count()
    completed_tasks = Task.objects.filter(user=user, status='completed').count()
    pending_tasks = total_tasks - completed_tasks
    
    # Get upcoming tasks (next 7 days)
    upcoming_date = timezone.now().date() + timezone.timedelta(days=7)
    upcoming_tasks = Task.objects.filter(
        user=user, 
        status='pending',
        due_date__lte=upcoming_date
    ).order_by('due_date')[:5]
    
    return render(request, 'dashboard.html', {
        'user': user,
        'full_name': user.full_name,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'upcoming_tasks': upcoming_tasks
    })

def lesson_plan(request):
    return render(request, 'lesson_plan.html')

def logout_view(request):
    """Logout user using Django's built-in logout"""
    # Clear any remaining registration data
    for key in list(request.session.keys()):
        if key.startswith("reg_"):
            del request.session[key]
    
    logout(request)  # Django's built-in logout function
    messages.success(request, "You have been logged out successfully.")
    return redirect('landing')

@login_required
def profile(request):
    user = request.user
    
    if request.method == 'POST':
        # Update all fields from the form
        user.first_name = request.POST.get('first_name', user.first_name)
        user.middle_name = request.POST.get('middle_name', user.middle_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.role = request.POST.get('role', user.role)
        user.rank = request.POST.get('rank', user.rank)
        user.department = request.POST.get('department', user.department)
        user.affiliations = request.POST.get('affiliations', user.affiliations)
        
        # Handle birth date
        dob = request.POST.get('dob')
        if dob:
            user.dob = dob
        
        try:
            user.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
        except Exception as e:
            messages.error(request, f"Error updating profile: {str(e)}")
    
    # GET request - show profile
    return render(request, 'profile.html', {
        'user': user,
        'full_name': user.full_name
    })

@login_required      
def lesson_planner(request):
    user = request.user
    return render(request, 'lesson_planner.html', {'user': user})

@login_required
def draft(request):
    user = request.user
    return render(request, 'draft.html', {'user': user})

@login_required
def task(request):
    user = request.user
    tasks = Task.objects.filter(user=user)
    
    # Handle filtering
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'completed':
        tasks = tasks.filter(status='completed')
    elif filter_type == 'pending':
        tasks = tasks.filter(status='pending')
    elif filter_type in ['high', 'medium', 'low']:
        tasks = tasks.filter(priority=filter_type)
    
    # Handle sorting
    sort_by = request.GET.get('sort', 'due-date')
    if sort_by == 'priority':
        # Custom ordering for priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        tasks = sorted(tasks, key=lambda x: priority_order[x.priority])
    elif sort_by == 'created':
        tasks = tasks.order_by('-created_at')
    elif sort_by == 'alphabetical':
        tasks = tasks.order_by('title')
    else:  # due-date (default)
        # Show tasks with due date first, then tasks without due date
        tasks = tasks.order_by('due_date', 'due_time')
    
    # Count completed tasks
    completed_count = Task.objects.filter(user=user, status='completed').count()
    total_count = Task.objects.filter(user=user).count()
    
    return render(request, 'task.html', {
        'user': user,
        'tasks': tasks,
        'completed_count': completed_count,
        'total_count': total_count,
        'current_filter': filter_type,
        'current_sort': sort_by
    })

@login_required
def Dep_Dash(request):
    user = request.user
    if user.role != "Department Head":
        messages.error(request, "You are not allowed to access this page.")
        return redirect('login')
    return render(request, 'Dep_Dash.html', {'user': user})

@login_required
def Dep_Faculty(request):
    user = request.user

    # Only allow Department Head
    if user.role != "Department Head":
        messages.error(request, "You are not allowed to access this page.")
        return redirect("dashboard")

    # Get all teachers and student teachers in the same department
    faculty_members = User.objects.filter(
        department=user.department,
        school=user.school,
        role__in=["Teacher", "Student Teacher"]
    ).order_by("role", "last_name")

    # Stats
    total_faculty = faculty_members.count()
    active_teachers = faculty_members.filter(role="Teacher").count()  # if you have a status field, add .filter(status="Active")
    student_teachers = faculty_members.filter(role="Student Teacher").count()
    pending_reviews = 0  # placeholder until you add LessonPlan or similar model

    return render(request, "Dep_Faculty.html", {
        "user": user,
        "faculty_members": faculty_members,
        "department": user.department,
        "total_faculty": total_faculty,
        "active_teachers": active_teachers,
        "student_teachers": student_teachers,
        "pending_reviews": pending_reviews,
    })



@login_required
def schedule(request):
    user = request.user
    return render(request, 'schedule/schedule.html', {'user': user})

class ScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Schedule.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

def Dep_Pending(request):
    return render(request, 'Dep_Pending.html')

def dep_template(request):
    return render(request, 'dep_template.html')

def teach_template(request):
    return render(request, 'teach_template.html')

@login_required
def st_dash(request):
    user = request.user
    if user.role != "Student Teacher":
        messages.error(request, "You are not allowed to access this page.")
        return redirect('login')
    return render(request, 'st_dash.html', {'user': user})

def calendar(request):
    return render(request, 'calendar.html')

def admin_calendar(request):
    return render(request, 'admin_calendar.html')

def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')

# def system_admin()

# Task API Views
@csrf_exempt
@require_POST
@login_required
def add_task_api(request):
    user = request.user
    
    try:
        data = json.loads(request.body)
        
        # Create new task
        task = Task(
            user=user,
            title=data.get('title'),
            description=data.get('description', ''),
            priority=data.get('priority', 'medium'),
            due_date=data.get('due_date'),
            due_time=data.get('due_time')
        )
        task.save()
        
        # Create notification
        notification = TaskNotification(
            user=user,
            task=task,
            notification_type='new',
            message=f'New task created: {task.title}'
        )
        notification.save()
        
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'priority': task.priority,
                'status': task.status,
                'due_date': task.formatted_due_date(),
                'display_due_date': task.display_due_date(),
                'display_due_datetime': task.display_due_datetime(),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
@login_required
def update_task_status_api(request, task_id):
    user = request.user
    
    try:
        task = get_object_or_404(Task, id=task_id, user=user)
        
        data = json.loads(request.body)
        new_status = data.get('status', 'pending')
        
        if new_status in ['pending', 'completed']:
            task.status = new_status
            task.save()
            
            # Create notification if task is completed
            if new_status == 'completed':
                notification = TaskNotification(
                    user=user,
                    task=task,
                    notification_type='completed',
                    message=f'Task completed: {task.title}'
                )
                notification.save()
            
            # Get updated counts
            completed_count = Task.objects.filter(user=user, status='completed').count()
            total_count = Task.objects.filter(user=user).count()
            
            return JsonResponse({
                'success': True,
                'completed_count': completed_count,
                'total_count': total_count
            })
        else:
            return JsonResponse({'success': False, 'error': 'Invalid status'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
@login_required
def delete_task_api(request, task_id):
    user = request.user
    
    try:
        task = get_object_or_404(Task, id=task_id, user=user)
        task.delete()
        
        # Get updated counts
        completed_count = Task.objects.filter(user=user, status='completed').count()
        total_count = Task.objects.filter(user=user).count()
        
        return JsonResponse({
            'success': True,
            'completed_count': completed_count,
            'total_count': total_count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_notifications_api(request):
    user = request.user
    
    try:
        notifications = TaskNotification.objects.filter(user=user, is_read=False).order_by('-created_at')[:10]
        
        notification_data = []
        for notification in notifications:
            notification_data.append({
                'id': notification.id,
                'type': notification.notification_type,
                'message': notification.message,
                'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
                'is_read': notification.is_read
            })
        
        return JsonResponse({'notifications': notification_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
@login_required
def mark_notification_read_api(request, notification_id):
    user = request.user
    
    try:
        notification = get_object_or_404(TaskNotification, id=notification_id, user=user)
        notification.is_read = True
        notification.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# Optional: Add some utility views for admin management
def admin_school_registrations(request):
    """Admin view to manage school registrations"""
    registrations = SchoolRegistration.objects.all().order_by('-created_at')
    
    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        registrations = registrations.filter(status=status_filter)
    
    context = {
        'registrations': registrations,
        'status_filter': status_filter,
        'status_choices': SchoolRegistration.STATUS_CHOICES,
    }
    
    return render(request, 'admin/school_registrations.html', context)

def admin_approve_registration(request, registration_id):
    """Admin view to approve/reject registrations"""
    if request.method == 'POST':
        try:
            registration = SchoolRegistration.objects.get(id=registration_id)
            action = request.POST.get('action')
            
            if action == 'approve':
                registration.approve_registration()
                messages.success(request, f"Registration for {registration.school_name} approved!")
            elif action == 'reject':
                reason = request.POST.get('reason', '')
                registration.reject_registration(reason=reason)
                messages.success(request, f"Registration for {registration.school_name} rejected.")
            
        except SchoolRegistration.DoesNotExist:
            messages.error(request, "Registration not found.")
    
    return redirect('admin_school_registrations')