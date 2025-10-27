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
# Add these imports at the top
from django.utils import timezone
from .models import LessonPlanSubmission
from lessonGenerator.models import LessonPlan
from django.shortcuts import redirect
from .models import User, Schedule, Task, TaskNotification, SchoolRegistration
from .serializers import ScheduleSerializer
from django.db.models import Q
from django.contrib.auth.decorators import user_passes_test 
import csv
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io
from .models import AdminLog, SystemSettings
from .forms import SchoolAdminRegistrationForm
logger = logging.getLogger(__name__)
from lessonlinkNotif.models import Notification
from django.http import HttpResponseForbidden
from functools import wraps

# School Registration Views

from django.contrib.auth.hashers import make_password


def restrict_user(usernames):
    """
    Decorator to restrict specific users from accessing views
    Usage: @restrict_user(['dep_dash', 'other_user'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.username in usernames:
                return HttpResponseForbidden("Access denied. You are not authorized to view this page.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator



def org_reg_1(request):
    """Handle school registration form - both GET and POST"""
    
    if request.method == 'GET':
        return render(request, 'org_reg/org_reg_1.html')
    
    elif request.method == 'POST':
        print("=== 🚀 FORM SUBMISSION DEBUG ===")
        print("📦 All POST data:", dict(request.POST))
        print("🔑 Password received:", request.POST.get('password'))
        print("📋 All POST keys:", list(request.POST.keys()))
        print("================================")
        try:
            # Extract form data - ADD PASSWORD
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
                'password': request.POST.get('password', '').strip(),  # ADD THIS
                'accuracy': request.POST.get('accuracy') == 'on',
                'terms': request.POST.get('terms') == 'on',
                'communications': request.POST.get('communications') == 'on',
            }

            # Debug the extracted data
            print("=== 📊 EXTRACTED FORM DATA ===")
            for key, value in form_data.items():
                print(f"{key}: {value}")
            print("==============================")
            
            # Validate required fields - ADD PASSWORD
            required_fields = [
                'school_name', 'school_id', 'address', 'province', 'region',
                'phone_number', 'email', 'contact_person', 'position',
                'contact_email', 'contact_phone', 'password'  # ADD PASSWORD
            ]
            
            missing_fields = []
            for field in required_fields:
                if not form_data[field]:
                    missing_fields.append(field.replace('_', ' ').title())
            
            if missing_fields:
                messages.error(request, f"Please complete the following required fields: {', '.join(missing_fields)}")
                return render(request, 'org_reg/org_reg_1.html', {'form_data': form_data})
            
            # Validate password strength
            password = form_data['password']
            if len(password) < 8:
                messages.error(request, "Password must be at least 8 characters long.")
                return render(request, 'org_reg/org_reg_1.html', {'form_data': form_data})
            
            # Check if school_id already exists
            if SchoolRegistration.objects.filter(school_id=form_data['school_id']).exists():
                messages.error(request, f"A school with ID '{form_data['school_id']}' is already registered.")
                return render(request, 'org_reg/org_reg_1.html', {'form_data': form_data})
            
            # Check if email already exists in User model
            if User.objects.filter(email=form_data['contact_email']).exists():
                messages.error(request, f"An account with email '{form_data['contact_email']}' already exists.")
                return render(request, 'org_reg/org_reg_1.html', {'form_data': form_data})
            
            # Create the school registration record first WITH HASHED PASSWORD
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
                password=make_password(form_data['password']),  # HASH THE PASSWORD
                accuracy=form_data['accuracy'],
                terms=form_data['terms'],
                communications=form_data['communications'],
                status='pending'
            )
            
            # Create a user account for the school admin
            try:
                # Split contact person name into first and last name
                name_parts = form_data['contact_person'].split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else "Admin"
                
                # In org_reg_1 view - Update user creation
                user = User.objects.create_user(
                    email=form_data['contact_email'],
                    password=form_data['password'],
                    first_name=first_name,
                    last_name=last_name,
                    role='Admin',  # Changed from 'Department Head' to 'Admin'
                    rank=form_data['position'],
                    department='Administration',
                    school=school_registration
                )
                
                # Log both creations
                logger.info(f"New school registration: {school_registration.school_name} ({school_registration.school_id})")
                logger.info(f"Created user account: {user.email} for school {school_registration.school_name}")
                
            except Exception as user_error:
                # If user creation fails, delete the school registration and show error
                school_registration.delete()
                logger.error(f"Failed to create user account: {str(user_error)}")
                messages.error(request, "Failed to create user account. Please try again.")
                return render(request, 'org_reg/org_reg_1.html', {'form_data': form_data})
            
            # Success message
            messages.success(
                request, 
                f"Registration submitted successfully! "
                f"Your application for {school_registration.school_name} has been received. "
                f"A temporary admin account has been created with email: {school_registration.contact_email}. "
                f"You will be contacted once your registration is reviewed."
            )
            
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


# def admin_get_calendar_activities(request):
#     """API endpoint to get calendar activities"""
#     # For now, return empty array - you can replace with database logic later
#     activities = []
#     return JsonResponse(activities, safe=False)

# def admin_add_calendar_activity(request):
#     """API endpoint to add calendar activity"""
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             # For now, just return a success response
#             # You can add database saving logic here later
#             return JsonResponse({'success': True, 'id': 1})
#         except Exception as e:
#             return JsonResponse({'success': False, 'error': str(e)}, status=400)
#     return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

# def admin_delete_calendar_activity(request, activity_id):
#     """API endpoint to delete calendar activity"""
#     if request.method == 'DELETE':
#         try:
#             # For now, just return success
#             # You can add database deletion logic here later
#             return JsonResponse({'success': True})
#         except Exception as e:
#             return JsonResponse({'success': False, 'error': str(e)}, status=400)
#     return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


# User Registration and Authentication Views
@login_required
def upload_profile_picture(request):
    """Handle profile picture upload via AJAX"""
    if request.method == 'POST' and request.FILES.get('profile_picture'):
        profile_picture = request.FILES['profile_picture']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if profile_picture.content_type not in allowed_types:
            return JsonResponse({
                'success': False, 
                'message': 'Invalid file type. Please upload JPG, PNG, GIF, or WebP.'
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
                except Exception as e:
                    print(f"Error deleting old profile picture: {e}")
                    # Continue with upload even if deletion fails
            
            # Generate unique filename
            file_extension = profile_picture.name.split('.')[-1].lower()
            if file_extension not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                file_extension = 'jpg'  # Default extension
            
            filename = f"profile_pictures/user_{user.id}_{uuid.uuid4().hex}.{file_extension}"
            
            # Save the file
            path = default_storage.save(filename, profile_picture)
            
            # Update user's profile picture
            user.profile_picture = path
            user.save()
            
            # Return the URL for the image
            image_url = user.profile_picture.url
            
            return JsonResponse({
                'success': True, 
                'image_url': image_url,
                'message': 'Profile picture uploaded successfully!'
            })
            
        except Exception as e:
            logger.error(f"Error uploading profile picture: {str(e)}")
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

@login_required
def admin_dep_faculty_management(request):
    """Admin faculty management view - shows Teachers and Department Heads from user's school"""
    user = request.user
    
    # Only allow admin users or department heads
    if not user.is_superuser and user.role != "Department Head":
        messages.error(request, "You are not authorized to access this page.")
        return redirect('dashboard')
    
    # Get ONLY Teachers and Department Heads from USER'S SCHOOL
    faculty_members = User.objects.filter(
        is_active=True,
        role__in=['Department Head', 'Teacher'],
        school=user.school  # ← FILTER BY USER'S SCHOOL
    ).select_related('school').order_by('department', 'last_name')
    
    print(f"DEBUG: Found {faculty_members.count()} faculty members from {user.school}")
    
    # Get unique departments from USER'S SCHOOL
    departments = User.objects.filter(
        is_active=True,
        department__isnull=False,
        school=user.school  # ← FILTER BY USER'S SCHOOL
    ).exclude(department='').values_list('department', flat=True).distinct().order_by('department')
    
    # Apply filters
    role_filter = request.GET.get('role', 'all')
    dept_filter = request.GET.get('department', 'all')
    search_query = request.GET.get('search', '')
    
    if role_filter != 'all':
        faculty_members = faculty_members.filter(role=role_filter)
    
    if dept_filter != 'all':
        faculty_members = faculty_members.filter(department=dept_filter)
    
    if search_query:
        faculty_members = faculty_members.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(department__icontains=search_query)
        )
    
    # Calculate statistics
    total_faculty = faculty_members.count()
    dept_heads = faculty_members.filter(role='Department Head').count()
    teachers = faculty_members.filter(role='Teacher').count()
    unique_departments = faculty_members.values_list('department', flat=True).distinct().count()
    
    # Prepare data for JavaScript
    faculty_data = []
    for faculty in faculty_members:
        if faculty.role == 'Department Head':
            subject = f"{faculty.department} Department Head"
        else:
            subject = faculty.department
        
        faculty_data.append({
            'name': faculty.full_name,
            'dept': faculty.department,
            'role': faculty.role,
            'subject': subject,
            'email': faculty.email,
            'status': 'Active' if faculty.is_active else 'Inactive',
            'school': faculty.school.school_name if faculty.school else 'Not assigned'
        })
    
    print(f"DEBUG: faculty_data has {len(faculty_data)} items from {user.school}")
    
    context = {
        'user': user,
        'faculty_members': faculty_members,
        'faculty_data_json': json.dumps(faculty_data),
        'departments': departments,
        'total_faculty': total_faculty,
        'dept_heads': dept_heads,
        'teachers': teachers,
        'unique_departments': unique_departments,
        'user_school': user.school.school_name if user.school else 'No School Assigned',  # Add school info
    }
    
    return render(request, 'admin_dep_faculty_management.html', context)
    

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
        role = request.session.get('reg_role')  # Get role from session
        
        # Get the school object
        try:
            school = SchoolRegistration.objects.get(id=school_id)
            school_name = school.school_name
        except (SchoolRegistration.DoesNotExist, ValueError):
            school_name = ""
            messages.error(request, "Please select a valid school.")

        # VALIDATION: Check if department head already exists for this department in this school
        if role == 'Department Head':
            existing_department_head = User.objects.filter(
                school=school,
                department=department,
                role='Department Head',
                is_active=True
            ).exists()
            
            if existing_department_head:
                messages.error(
                    request, 
                    f'A Department Head already exists for {department} in {school.school_name}. '
                    f'Please choose a different department or contact the administrator.'
                )
                return render(request, 'registration/registration_4.html', {
                    'department': department,
                    'school': school_id,
                    'affiliations': affiliations,
                    'schools': approved_schools,
                    'error_message': f'A Department Head already exists for {department} in {school.school_name}.',
                    'show_error': True
                })

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
                school=school,  # Store the school object
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

@csrf_exempt
def check_department_head(request):
    """AJAX endpoint to check if department head already exists for a department in a school"""
    school_id = request.GET.get('school')
    department = request.GET.get('department')
    
    if not school_id or not department:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    try:
        school = SchoolRegistration.objects.get(id=school_id)
        
        # Check if department head already exists
        exists = User.objects.filter(
            school=school,
            department=department,
            role='Department Head',
            is_active=True
        ).exists()
        
        return JsonResponse({'exists': exists})
    
    except SchoolRegistration.DoesNotExist:
        return JsonResponse({'error': 'School not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
        
    
def registration_5(request):
    return render(request, 'registration/registration_5.html')

def login_view(request):
    print("🟢 LOGIN VIEW CALLED")
    print(f"🟢 GET parameters: {request.GET}")
    print(f"🟢 timeout parameter: {request.GET.get('timeout')}")
    
    # ✅ Check for timeout parameter and add to context
    show_timeout_message = request.GET.get('timeout') == '1'
    print(f"🟢 show_timeout_message: {show_timeout_message}")

    # ✅ Check for timeout parameter and add to context
    show_timeout_message = request.GET.get('timeout') == '1'
    
    # If user is already logged in, redirect based on role
    if request.user.is_authenticated:
        return redirect_based_on_role(request.user)

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        errors = {}
        show_error = False

        # Basic validation
        if not email:
            errors['email'] = True
            errors['email_message'] = "Email address is required"
            show_error = True

        if not password:
            errors['password'] = True
            errors['password_message'] = "Password is required"
            show_error = True

        if not errors:
            # Regular user authentication
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect_based_on_role(user)

            # Try school admin authentication
            school_admin = try_school_admin_login(email, password)
            if school_admin:
                login(request, school_admin)
                return redirect_based_on_role(school_admin)

            # Authentication failed - detect reason
            try:
                user_exists = User.objects.filter(email=email).exists()
                if user_exists:
                    errors['authentication'] = True
                    errors['authentication_message'] = "Invalid password. Please try again."
                else:
                    school_exists = SchoolRegistration.objects.filter(
                        Q(contact_email=email) | Q(email=email)
                    ).exists()
                    if school_exists:
                        errors['authentication'] = True
                        errors['authentication_message'] = "Invalid password for this school account. Please try again."
                    else:
                        errors['email'] = True
                        errors['email_message'] = "No account found with this email. Please register first."
                show_error = True
            except Exception:
                errors['authentication'] = True
                errors['authentication_message'] = "An error occurred during authentication. Please try again."
                show_error = True

        # Render with errors
        context = {
            'email': email, 
            'show_error': show_error,
            'show_timeout_message': show_timeout_message  # ✅ Add this
        }
        context.update(errors)
        return render(request, 'login.html', context)

    # GET request
    context = {'show_timeout_message': show_timeout_message}  # ✅ Add this
    return render(request, 'login.html', context)


    

def redirect_based_on_role(user):
    """Redirect user based on their role - UPDATED TO CHECK SUPERUSER FIRST"""
    print(f"DEBUG redirect_based_on_role: User {user.email} - Role: {user.role} - Superuser: {user.is_superuser}")
    
    # CHECK SUPERUSER FIRST - This is the fix!
    if user.is_superuser:
        print("  -> Redirecting to super_user_dashboard (SUPERUSER)")
        return redirect('super_user_dashboard')
    elif user.role == "Student Teacher":
        print("  -> Redirecting to st_dash")
        return redirect('st_dash')
    elif user.role == "Department Head":
        print("  -> Redirecting to Dep_Dash")
        return redirect('Dep_Dash')
    elif user.role == "Teacher":
        print("  -> Redirecting to dashboard")
        return redirect('dashboard')
    elif user.role in ["Admin", "Supervisor"]:
        print("  -> Redirecting to admin_dashboard")
        return redirect('admin_dashboard')
    else:
        print(f"  -> Unknown role '{user.role}', redirecting to dashboard")
        return redirect('dashboard')

def try_school_admin_login(email, password):
    """Try to authenticate as school admin using SchoolRegistration credentials"""
    try:
        # Check if this email exists in SchoolRegistration (both contact_email and email fields)
        school_reg = SchoolRegistration.objects.filter(
            Q(contact_email=email) | Q(email=email),
            status='approved'  # Only allow approved schools
        ).first()
        
        if school_reg:
            # Check password directly (since SchoolRegistration stores hashed password)
            from django.contrib.auth.hashers import check_password
            if check_password(password, school_reg.password):
                # Find or create user account for this school admin
                user, created = User.objects.get_or_create(
                    email=school_reg.contact_email,  # Use contact_email as primary email
                    defaults={
                        'first_name': school_reg.contact_person.split(' ', 1)[0] if ' ' in school_reg.contact_person else school_reg.contact_person,
                        'last_name': school_reg.contact_person.split(' ', 1)[1] if ' ' in school_reg.contact_person else 'Admin',
                        'role': 'Department Head',
                        'rank': school_reg.position,
                        'department': 'Administration',
                        'school': school_reg,
                        'is_active': True
                    }
                )
                
                if created:
                    # Set password for the user account
                    user.set_password(password)
                    user.save()
                    print(f"Created new user account for school admin: {user.email}")
                
                return user
    except Exception as e:
        print(f"School admin login error: {e}")
    
    return None



def redirect_based_on_role(user):
    """Redirect user based on their role - UPDATED TO CHECK SUPERUSER FIRST"""
    print(f"DEBUG redirect_based_on_role: User {user.email} - Role: {user.role} - Superuser: {user.is_superuser}")
    
    # CHECK SUPERUSER FIRST - This is the fix!
    if user.is_superuser:
        print("  -> Redirecting to super_user_dashboard (SUPERUSER)")
        return redirect('super_user_dashboard')  # This requires 'redirect' import
    elif user.role == "Student Teacher":
        print("  -> Redirecting to st_dash")
        return redirect('st_dash')
    elif user.role == "Department Head":
        print("  -> Redirecting to Dep_Dash")
        return redirect('Dep_Dash')
    elif user.role == "Teacher":
        print("  -> Redirecting to dashboard")
        return redirect('dashboard')
    elif user.role in ["Admin", "Supervisor"]:
        print("  -> Redirecting to admin_dashboard")
        return redirect('admin_dashboard')
    else:
        print(f"  -> Unknown role '{user.role}', redirecting to dashboard")
        return redirect('dashboard')

        

def try_school_admin_login(email, password):
    """Try to authenticate as school admin using SchoolRegistration credentials - ONLY APPROVED SCHOOLS"""
    try:
        # Only allow approved schools to login
        school_reg = SchoolRegistration.objects.filter(
            Q(contact_email=email) | Q(email=email),
            status='approved'  # ← KEEP THIS - ONLY APPROVED SCHOOLS CAN LOGIN
        ).first()
        
        if school_reg:
            # Check password directly
            from django.contrib.auth.hashers import check_password
            if check_password(password, school_reg.password):
                # Find or create user account
                user = User.objects.filter(
                    Q(email=school_reg.contact_email) | Q(school=school_reg),
                    role__in=['Department Head', 'Admin']
                ).first()
                
                if user:
                    print(f"Found existing user: {user.email} with role: {user.role}")
                    return user
                else:
                    # Create new user account for school admin
                    name_parts = school_reg.contact_person.split(' ', 1)
                    first_name = name_parts[0]
                    last_name = name_parts[1] if len(name_parts) > 1 else "Admin"
                    
                    user = User.objects.create_user(
                        email=school_reg.contact_email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        role='Department Head',
                        rank=school_reg.position,
                        department='Administration',
                        school=school_reg,
                        is_active=True
                    )
                    print(f"Created new user account for school admin: {user.email}")
                    return user
                    
    except Exception as e:
        print(f"School admin login error: {e}")
    
    return None

@login_required
def dashboard(request):
    # ROLE-BASED REDIRECTS - ADD THIS
    if hasattr(request, 'user') and request.user.is_authenticated:
        user_role = request.user.role
        
        if user_role == "Department Head":
            messages.info(request, "Redirected to Department Head dashboard")
            return redirect('Dep_Dash')
        elif user_role == "Student Teacher":
            messages.info(request, "Redirected to Student Teacher dashboard")
            return redirect('st_dash')
        elif user_role in ["Admin", "Supervisor"]:
            messages.info(request, "Redirected to Admin dashboard")
            return redirect('admin_dashboard')
        # Teachers will continue to the regular dashboard
    
    user = request.user
    
    # Add welcome message here instead of login
    if not request.session.get('welcome_shown'):
        messages.success(request, f"Welcome back, {user.first_name}!")
        request.session['welcome_shown'] = True
    
    # Get lesson plan statistics for dashboard
    from lessonGenerator.models import LessonPlan
    
    # Total Lesson Plans (all lesson plans for the user)
    total_lesson_plans = LessonPlan.objects.filter(created_by=user).count()
    
    # Draft Lesson Plans (only those with draft status)
    draft_lesson_plans = LessonPlan.objects.filter(created_by=user, status='draft').count()
    
    # Get task statistics for dashboard
    total_tasks = Task.objects.filter(user=user).count()
    
    # Get recent lesson plans (5 most recent)
    recent_lesson_plans = LessonPlan.objects.filter(created_by=user).order_by('-created_at')[:5]
    
    # Get today's schedule
    from django.utils import timezone
    import datetime
    
    # Get the current day name (e.g., 'monday', 'tuesday')
    today = timezone.now().strftime('%A').lower()
    
    # Get today's schedule for the user
    todays_schedule = Schedule.objects.filter(user=user, day=today).order_by('time')
    
    return render(request, 'dashboard.html', {
        'user': user,
        'full_name': user.full_name,
        'total_tasks': total_tasks,
        'total_lesson_plans': total_lesson_plans,
        'draft_lesson_plans': draft_lesson_plans,
        'recent_lesson_plans': recent_lesson_plans,
        'todays_schedule': todays_schedule
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


# ====================================================== SUPER USER SCHOOL APPROVAL ======================================================

def is_superuser(user):
    """Check if user is superuser"""
    return user.is_authenticated and user.is_superuser

@login_required
@user_passes_test(is_superuser)
def super_user_dashboard(request):
    """Super user dashboard for managing school approvals"""
    user = request.user
    
    # Get all schools for statistics
    total_schools = SchoolRegistration.objects.count()
    pending_schools = SchoolRegistration.objects.filter(status='pending')
    approved_schools = SchoolRegistration.objects.filter(status='approved')
    rejected_schools = SchoolRegistration.objects.filter(status='rejected')
    
    # Get admin counts for approved schools
    from .models import SchoolAdmin
    approved_schools_with_admin_count = []
    for school in approved_schools:
        admin_count = SchoolAdmin.objects.filter(school=school, is_active=True).count()
        approved_schools_with_admin_count.append({
            'school': school,
            'admin_count': admin_count
        })
    
    # Get recent activities
    recent_approvals = SchoolRegistration.objects.filter(
        status__in=['approved', 'rejected']
    ).order_by('-updated_at')[:5]
    
    context = {
        'pending_schools': pending_schools,
        'approved_schools': approved_schools,
        'approved_schools_with_admin_count': approved_schools_with_admin_count,  # Add this
        'rejected_schools': rejected_schools,
        'recent_approvals': recent_approvals,
        'total_schools': total_schools,
        'pending_schools_count': pending_schools.count(),
        'approved_schools_count': approved_schools.count(),
        'rejected_schools_count': rejected_schools.count(),
    }
    return render(request, 'super_user.html', context)

@login_required
@user_passes_test(is_superuser)
def approve_school(request, school_id):
    """Approve a school registration"""
    if request.method == 'POST':
        try:
            school = get_object_or_404(SchoolRegistration, id=school_id)
            school.status = 'approved'
            school.save()
            
            # Log the action
            AdminLog.objects.create(
                admin=request.user,
                action='school_approved',
                description=f"Approved school: {school.school_name} (ID: {school.school_id})",
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'School "{school.school_name}" has been approved successfully!')
            
        except SchoolRegistration.DoesNotExist:
            messages.error(request, "School not found.")
        except Exception as e:
            messages.error(request, f"Error approving school: {str(e)}")
    
    return redirect('super_user_dashboard')

@login_required
@user_passes_test(is_superuser)
def reject_school(request, school_id):
    """Reject a school registration"""
    if request.method == 'POST':
        try:
            school = get_object_or_404(SchoolRegistration, id=school_id)
            school.status = 'rejected'
            school.save()
            
            # Log the action
            AdminLog.objects.create(
                admin=request.user,
                action='school_rejected',
                description=f"Rejected school: {school.school_name} (ID: {school.school_id})",
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'School "{school.school_name}" has been rejected.')
            
        except SchoolRegistration.DoesNotExist:
            messages.error(request, "School not found.")
        except Exception as e:
            messages.error(request, f"Error rejecting school: {str(e)}")
    
    return redirect('super_user_dashboard')

@login_required
@user_passes_test(is_superuser)
def super_user_school_detail(request, school_id):
    """View detailed school information"""
    school = get_object_or_404(SchoolRegistration, id=school_id)
    
    # Get users associated with this school
    school_users = User.objects.filter(school=school).order_by('role', 'last_name')
    
    context = {
        'school': school,
        'school_users': school_users,
        'users_count': school_users.count(),
    }
    
    return render(request, 'super_user_school_detail.html', context)


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
    # ROLE-BASED REDIRECTS - ADD THIS
    if hasattr(request, 'user') and request.user.is_authenticated:
        user_role = request.user.role
        
        if user_role == "Student Teacher":
            messages.info(request, "Redirected to Student Teacher dashboard")
            return redirect('st_dash')
        elif user_role == "Teacher":
            messages.info(request, "Redirected to Teacher dashboard")
            return redirect('dashboard')
        elif user_role in ["Admin", "Supervisor"]:
            messages.info(request, "Redirected to Admin dashboard")
            return redirect('admin_dashboard')
        # Department Heads will continue to their dashboard
    
    user = request.user
    if user.role != "Department Head":
        messages.error(request, "You are not allowed to access this page.")
        return redirect('login')
    
    # Add welcome message here instead of login
    if not request.session.get('welcome_shown'):
        messages.success(request, f"Welcome back, {user.first_name}!")
        request.session['welcome_shown'] = True
    
    # Get dynamic statistics for department head dashboard
    
    # 1. Pending Reviews - Count from pending submissions
    pending_reviews_count = LessonPlanSubmission.objects.filter(
        submitted_to=user,
        status='submitted'
    ).count()
    
    # 2. Total Faculty - Count from faculty in same department and school
    total_faculty_count = User.objects.filter(
        department=user.department,
        school=user.school,
        role__in=['Teacher', 'Student Teacher'],
        is_active=True
    ).count()
    
    # 3. My Lesson Plans - Count lesson plans created by department head
    from lessonGenerator.models import LessonPlan
    my_lesson_plans_count = LessonPlan.objects.filter(
        created_by=user
    ).count()
    
    # 4. Pending Lesson Plan Reviews - Get actual pending submissions for the card
    pending_submissions = LessonPlanSubmission.objects.filter(
        submitted_to=user,
        status='submitted'
    ).select_related('lesson_plan', 'submitted_by').order_by('submission_date')[:3]
    
    return render(request, 'Dep_Dash.html', {
        'user': user,
        'pending_reviews_count': pending_reviews_count,
        'total_faculty_count': total_faculty_count,
        'my_lesson_plans_count': my_lesson_plans_count,
        'pending_submissions': pending_submissions
    })

@login_required
def Dep_Faculty(request):
    user = request.user

    # Only allow Department Head
    if user.role != "Department Head":
        messages.error(request, "You are not allowed to access this page.")
        return redirect("dashboard")

    # Get all teachers and student teachers in the same department and school
    faculty_members = User.objects.filter(
        department=user.department,
        school=user.school,
        role__in=["Teacher", "Student Teacher"],
        is_active=True
    ).order_by("role", "last_name")

    # Calculate real-time statistics
    total_faculty = faculty_members.count()
    active_teachers = faculty_members.filter(role="Teacher").count()
    student_teachers = faculty_members.filter(role="Student Teacher").count()
    
    # Calculate pending reviews for each faculty member
    from lessonGenerator.models import LessonPlan
    from .models import LessonPlanSubmission
    
    # Get total pending reviews for the department
    pending_reviews = LessonPlanSubmission.objects.filter(
        submitted_to=user,
        status='submitted'
    ).count()

    # Add additional statistics to each faculty member
    faculty_with_stats = []
    for member in faculty_members:
        # Get pending reviews for this faculty member
        member_pending_reviews = LessonPlanSubmission.objects.filter(
            submitted_by=member,
            status='submitted'
        ).count()
        
        # Get last active time (use last_login if available, otherwise use date_joined)
        last_active = member.last_login if member.last_login else member.date_joined
        
        faculty_with_stats.append({
            'user': member,
            'pending_reviews': member_pending_reviews,
            'last_active': last_active,
            'is_active': member.is_active and member.last_login and (timezone.now() - member.last_login).days < 30
        })

    return render(request, "Dep_Faculty.html", {
        "user": user,
        "faculty_members": faculty_with_stats,
        "department": user.department,
        "total_faculty": total_faculty,
        "active_teachers": active_teachers,
        "student_teachers": student_teachers,
        "pending_reviews": pending_reviews,
    })

def dep_calendar(request):
    user = request.user
    # Allow both Department Heads and Teachers to access
    if user.role not in ["Department Head", "Teacher", "Student Teacher"]:
        messages.error(request, "You are not allowed to access this page.")
        return redirect('dashboard')
    
    # DEBUG: Print user info to console
    print(f"CALENDAR ACCESS: User {user.email} - Role: {user.role} - Superuser: {user.is_superuser}")
    
    # Set user_role based on actual user role
    if user.is_superuser:
        user_role = 'admin'
    elif user.role == "Department Head":
        user_role = 'department_head'
    else:  # Teacher or Student Teacher
        user_role = 'teacher'
    
    context = {
        'user': user,
        'user_role': user_role
    }
    return render(request, 'dep_calendar.html', context)

def teacher_calendar(request):
    user = request.user
    # Only allow Teachers and Student Teachers
    if user.role not in ["Teacher", "Student Teacher"]:
        messages.error(request, "You are not allowed to access this page.")
        return redirect('dashboard')
    
    context = {
        'user': user,
        'user_role': 'teacher'
    }
    return render(request, 'teacher_calendar.html', context)


@login_required
@user_passes_test(is_superuser)
def register_school_admin(request, school_id):
    """Register a new school admin for an approved school"""
    school = get_object_or_404(SchoolRegistration, id=school_id, status='approved')
    
    if request.method == 'POST':
        # Use manual form processing instead of form class temporarily
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Manual validation
        errors = []
        if not all([first_name, last_name, email, password, confirm_password]):
            errors.append("All fields are required.")
        
        if password != confirm_password:
            errors.append("Passwords do not match.")
        
        if User.objects.filter(email=email).exists():
            errors.append("A user with this email already exists.")
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'register_school_admin.html', {
                'school': school,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
            })
        
        try:
            # Create user account
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=True,
                role='Admin',
                department='Administration',
                school=school
            )
            
            # Create school admin relationship
            from .models import SchoolAdmin
            school_admin = SchoolAdmin.objects.create(
                user=user,
                school=school,
                created_by=request.user
            )
            
            # Log the action
            AdminLog.objects.create(
                admin=request.user,
                action='school_admin_created',
                description=f"Created school admin '{email}' for {school.school_name}",
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f"School admin '{email}' created successfully for {school.school_name}")
            return redirect('super_user_dashboard')
            
        except Exception as e:
            messages.error(request, f"Error creating school admin: {str(e)}")
    
    # GET request - show empty form
    return render(request, 'register_school_admin.html', {
        'school': school
    })

@login_required
@user_passes_test(is_superuser)
def school_admin_list(request, school_id):
    """View all admins for a specific school"""
    school = get_object_or_404(SchoolRegistration, id=school_id)
    
    # Get all school admins for this school
    from .models import SchoolAdmin
    admins = SchoolAdmin.objects.filter(school=school).select_related('user', 'created_by')
    
    return render(request, 'school_admin_list.html', {
        'school': school,
        'admins': admins
    })

@login_required
@user_passes_test(is_superuser)
def activate_school_admin(request, admin_id):
    """Activate a school admin"""
    if request.method == 'POST':
        try:
            from .models import SchoolAdmin
            school_admin = get_object_or_404(SchoolAdmin, id=admin_id)
            school_admin.is_active = True
            school_admin.user.is_active = True
            school_admin.user.save()
            school_admin.save()
            
            # Log the action
            AdminLog.objects.create(
                admin=request.user,
                action='school_admin_activated',
                description=f"Activated school admin '{school_admin.user.username}' for {school_admin.school.school_name}",
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f"School admin '{school_admin.user.username}' has been activated.")
            
        except Exception as e:
            messages.error(request, f"Error activating school admin: {str(e)}")
    
    return redirect('school_admin_list', school_id=school_admin.school.id)

@login_required
@user_passes_test(is_superuser)
def deactivate_school_admin(request, admin_id):
    """Deactivate a school admin"""
    if request.method == 'POST':
        try:
            from .models import SchoolAdmin
            school_admin = get_object_or_404(SchoolAdmin, id=admin_id)
            school_admin.is_active = False
            school_admin.user.is_active = False
            school_admin.user.save()
            school_admin.save()
            
            # Log the action
            AdminLog.objects.create(
                admin=request.user,
                action='school_admin_deactivated',
                description=f"Deactivated school admin '{school_admin.user.username}' from {school_admin.school.school_name}",
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f"School admin '{school_admin.user.username}' has been deactivated.")
            
        except Exception as e:
            messages.error(request, f"Error deactivating school admin: {str(e)}")
    
    return redirect('school_admin_list', school_id=school_admin.school.id)




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
    
    # Add welcome message here instead of login
    if not request.session.get('welcome_shown'):
        messages.success(request, f"Welcome back, {user.first_name}!")
        request.session['welcome_shown'] = True
    
    return render(request, 'st_dash.html', {'user': user})

def calendar(request):
    return render(request, 'calendar.html')

def admin_calendar(request):
    context = {
        'user': request.user,
        'user_role': 'admin'  # This makes the template show admin permissions
    }
    return render(request, 'dep_calendar.html', context)

@login_required
def admin_dashboard(request):
    # ROLE-BASED REDIRECTS - ADD THIS
    if hasattr(request, 'user') and request.user.is_authenticated:
        user_role = request.user.role
        
        if user_role == "Department Head":
            messages.info(request, "Redirected to Department Head dashboard")
            return redirect('Dep_Dash')
        elif user_role == "Student Teacher":
            messages.info(request, "Redirected to Student Teacher dashboard")
            return redirect('st_dash')
        elif user_role == "Teacher":
            messages.info(request, "Redirected to Teacher dashboard")
            return redirect('dashboard')
        # Admins and Supervisors will continue to the admin dashboard
    
    """Enhanced admin dashboard with real data"""
    user = request.user
    
    # Get the school for the logged-in admin
    school = None
    
    # Try different ways to get the school
    if user.school:
        school = user.school
    elif hasattr(user, 'schoolregistration'):
        school = user.schoolregistration
    else:
        # Try to find school by admin's email
        school = SchoolRegistration.objects.filter(
            Q(contact_email=user.email) | Q(email=user.email)
        ).first()
    
    # If no school found, get the first one (fallback)
    if not school:
        school = SchoolRegistration.objects.first()

    # Get real statistics
    if school:
        # School-specific statistics
        total_users = User.objects.filter(school=school).count()
        teachers_count = User.objects.filter(school=school, role='Teacher').count()
        dept_heads_count = User.objects.filter(school=school, role='Department Head').count()
        student_teachers_count = User.objects.filter(school=school, role='Student Teacher').count()
        total_lessons = LessonPlan.objects.filter(created_by__school=school).count()
        approved_lessons = LessonPlan.objects.filter(created_by__school=school, status='final').count()
        draft_lessons = LessonPlan.objects.filter(created_by__school=school, status='draft').count()
        
        # Recent activities for this school
        recent_lessons = LessonPlan.objects.filter(created_by__school=school).order_by('-created_at')[:5]
        recent_users = User.objects.filter(school=school).order_by('-date_joined')[:5]
        
        # Calculate growth (you can implement more sophisticated logic)
        user_growth = "+12%"  # Placeholder - implement your growth logic
        lesson_growth = "+5%"  # Placeholder
        
    else:
        # System-wide statistics (super admin view)
        total_users = User.objects.count()
        teachers_count = User.objects.filter(role='Teacher').count()
        dept_heads_count = User.objects.filter(role='Department Head').count()
        student_teachers_count = User.objects.filter(role='Student Teacher').count()
        total_lessons = LessonPlan.objects.count()
        approved_lessons = LessonPlan.objects.filter(status='final').count()
        draft_lessons = LessonPlan.objects.filter(status='draft').count()
        total_schools = SchoolRegistration.objects.count()
        approved_schools = SchoolRegistration.objects.filter(status='approved').count()
        
        # Recent activities
        recent_lessons = LessonPlan.objects.select_related('created_by').order_by('-created_at')[:5]
        recent_users = User.objects.select_related('school').order_by('-date_joined')[:5]
        
        user_growth = "+8%"
        lesson_growth = "+12%"

    # Get pending submissions for department heads
    pending_submissions = 0
    if user.role == 'Department Head':
        pending_submissions = LessonPlanSubmission.objects.filter(
            submitted_to=user, 
            status='submitted'
        ).count()

    context = {
        "SchoolRegistration": school,
        'school': school,
        'user': user,
        
        # Real statistics
        'total_users': total_users,
        'teachers_count': teachers_count,
        'dept_heads_count': dept_heads_count,
        'student_teachers_count': student_teachers_count,
        'total_lessons': total_lessons,
        'approved_lessons': approved_lessons,
        'draft_lessons': draft_lessons,
        'pending_submissions': pending_submissions,
        
        # Growth metrics
        'user_growth': user_growth,
        'lesson_growth': lesson_growth,
        
        # Recent activities
        'recent_lessons': recent_lessons,
        'recent_users': recent_users,
        
        # System-wide stats (for super admin)
        'total_schools': total_schools if not school else 0,
        'approved_schools': approved_schools if not school else 0,
        
        'is_admin': user.role in ['Admin', 'Department Head', 'Supervisor'],
        'user_role': user.role,
    }
    
    return render(request, 'admin_dashboard.html', context)


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



@login_required
def submit_lesson_plan(request, lesson_plan_id):
    """Submit a lesson plan to department head for approval"""
    if request.method == 'POST':
        try:
            # Get the lesson plan
            lesson_plan = LessonPlan.objects.get(id=lesson_plan_id, created_by=request.user)
            
            # Validate that the teacher has a school and department
            if not request.user.school:
                messages.error(request, "You are not assigned to any school. Please contact administrator.")
                return redirect('draft_list')
            
            if not request.user.department:
                messages.error(request, "You are not assigned to any department. Please contact administrator.")
                return redirect('draft_list')
            
            # Find the correct department head - ensure same school and department
            department_head = User.objects.filter(
                role='Department Head',
                department=request.user.department,
                school=request.user.school,
                is_active=True
            ).first()
            
            if not department_head:
                # Provide helpful error message
                messages.error(request, 
                    f"No active Department Head found for {request.user.department} department in {request.user.school}. "
                    "Please contact administrator."
                )
                return redirect('draft_list')
            
            # Use the model method to handle submission
            success, message = lesson_plan.submit_for_approval(department_head)
            
            if success:
                # Create submission notification for department head
                from lessonlinkNotif.models import Notification
                Notification.create_lesson_submitted_notification(
                    LessonPlanSubmission.objects.get(
                        lesson_plan=lesson_plan,
                        submitted_to=department_head,
                        status='submitted'
                    )
                )
                
                # Change lesson plan status to final when submitted
                lesson_plan.status = LessonPlan.FINAL
                lesson_plan.save()
                messages.success(request, message)
                
            else:
                messages.error(request, message)
                
        except LessonPlan.DoesNotExist:
            messages.error(request, "Lesson plan not found or you don't have permission to submit it.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
        
        return redirect('draft_list')
    
    return redirect('dashboard')

@login_required
def Dep_Pending(request):
    """Department head's pending reviews page"""
    user = request.user
    
    # Only department heads can access this page
    if user.role != "Department Head":
        messages.error(request, "You are not authorized to access this page.")
        return redirect('dashboard')
    
    # Validate that department head has school and department assigned
    if not user.school or not user.department:
        messages.error(request, "Your account is missing school or department information. Please contact administrator.")
        return redirect('dashboard')
    
    # Get pending submissions for this department head (with validation)
    pending_submissions = LessonPlanSubmission.objects.filter(
        submitted_to=user,
        status='submitted'
    ).select_related('lesson_plan', 'submitted_by').order_by('submission_date')
    
    # Additional validation: filter only valid submissions (same school/department)
    valid_submissions = []
    for submission in pending_submissions:
        # Double-check that the submission is valid
        if (submission.submitted_by.school == user.school and 
            submission.submitted_by.department == user.department):
            valid_submissions.append(submission)
        else:
            # Log invalid submissions (shouldn't happen due to model validation)
            print(f"INVALID SUBMISSION: {submission.id} - School/Department mismatch")
    
    # Get reviewed submissions for history
    reviewed_submissions = LessonPlanSubmission.objects.filter(
        submitted_to=user
    ).exclude(status='submitted').select_related('lesson_plan', 'submitted_by').order_by('-review_date')[:10]
    
    return render(request, 'Dep_Pending.html', {
        'user': user,
        'pending_submissions': valid_submissions,
        'reviewed_submissions': reviewed_submissions,
        'pending_count': len(valid_submissions),
        'user_school': user.school,
        'user_department': user.department
    })

@login_required
def review_lesson_plan(request, submission_id):
    """Department head reviews a lesson plan"""
    if request.method == 'POST':
        try:
            submission = LessonPlanSubmission.objects.get(
                id=submission_id,
                submitted_to=request.user
            )
            
            action = request.POST.get('action')
            review_notes = request.POST.get('review_notes', '').strip()
            
            if action == 'approve':
                submission.status = 'approved'
                submission.lesson_plan.status = LessonPlan.FINAL
                
                # Create approval notification
                Notification.create_draft_status_notification(submission, approved=True)
                
                messages.success(request, f"Lesson plan '{submission.lesson_plan.title}' approved successfully!")
            elif action == 'reject':
                submission.status = 'rejected'
                
                # Create rejection notification
                Notification.create_draft_status_notification(submission, approved=False)
                
                messages.success(request, f"Lesson plan '{submission.lesson_plan.title}' rejected.")
            elif action == 'needs_revision':
                submission.status = 'needs_revision'
                
                # Create needs revision notification
                Notification.create_draft_status_notification(submission, approved=False)
                
                messages.success(request, f"Lesson plan '{submission.lesson_plan.title}' returned for revision.")
            
            submission.review_notes = review_notes
            submission.review_date = timezone.now()
            submission.save()
            submission.lesson_plan.save()
            
        except LessonPlanSubmission.DoesNotExist:
            messages.error(request, "Submission not found.")
        
        return redirect('Dep_Pending')
    
    return redirect('dashboard')

@login_required
def lesson_plan_detail(request, submission_id):
    """View lesson plan details for review"""
    try:
        submission = LessonPlanSubmission.objects.get(id=submission_id)
        
        # Check if user has permission to view
        if request.user != submission.submitted_to and request.user != submission.submitted_by:
            messages.error(request, "You are not authorized to view this lesson plan.")
            return redirect('dashboard')
        
        # Get structured content for the template
        structured_content = submission.lesson_plan.get_structured_content()
        
        return render(request, 'lesson_plan_detail.html', {
            'submission': submission,
            'lesson_plan': submission.lesson_plan,
            'structured_content': structured_content,
            'can_review': request.user == submission.submitted_to and submission.status == 'submitted'
        })
        
    except LessonPlanSubmission.DoesNotExist:
        messages.error(request, "Lesson plan not found.")
        return redirect('dashboard')

# ======================================================ADMIN===============================================================================================
# ==========================================================================================================================================================

def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and (user.role == 'Admin' or user.is_superuser)

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@login_required
@user_passes_test(is_admin)
def admin_user_management(request):
    """Admin user management - view all users in their school"""
    user = request.user
    
    # Get users from admin's school only
    users = User.objects.filter(school=user.school).select_related('school').order_by('role', 'last_name')
    
    # Apply filters
    role_filter = request.GET.get('role', 'all')
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    
    if role_filter != 'all':
        users = users.filter(role=role_filter)
    
    if status_filter != 'all':
        users = users.filter(is_active=status_filter == 'active')
    
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(department__icontains=search_query)
        )
    
    # Calculate statistics
    total_users = users.count()
    active_users = users.filter(is_active=True).count()
    inactive_users = users.filter(is_active=False).count()
    departments_count = users.values_list('department', flat=True).distinct().count()
    
    context = {
        'users': users,
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'departments_count': departments_count,
        'role_choices': User.ROLE_CHOICES,
        'user_school': user.school,
    }
    
    return render(request, 'admin/admin_user_management.html', context)

@login_required
@user_passes_test(is_admin)
def admin_edit_user(request, user_id):
    """Admin edit user details"""
    admin_user = request.user
    user_to_edit = get_object_or_404(User, id=user_id, school=admin_user.school)
    
    if request.method == 'POST':
        # Update user fields
        user_to_edit.first_name = request.POST.get('first_name', user_to_edit.first_name)
        user_to_edit.last_name = request.POST.get('last_name', user_to_edit.last_name)
        user_to_edit.role = request.POST.get('role', user_to_edit.role)
        user_to_edit.department = request.POST.get('department', user_to_edit.department)
        user_to_edit.rank = request.POST.get('rank', user_to_edit.rank)
        user_to_edit.is_active = request.POST.get('is_active') == 'on'
        
        try:
            user_to_edit.save()
            
            # Log the action
            AdminLog.objects.create(
                admin=admin_user,
                action='user_modified',
                target_user=user_to_edit,
                description=f"Modified user {user_to_edit.email}",
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f"User {user_to_edit.email} updated successfully!")
            return redirect('admin_user_management')
            
        except Exception as e:
            messages.error(request, f"Error updating user: {str(e)}")
    
    return render(request, 'admin/admin_edit_user.html', {
        'user_to_edit': user_to_edit,
        'role_choices': User.ROLE_CHOICES,
    })

@login_required
@user_passes_test(is_admin)
def admin_reset_password(request, user_id):
    """Admin reset user password"""
    if request.method == 'POST':
        admin_user = request.user
        user_to_reset = get_object_or_404(User, id=user_id, school=admin_user.school)
        
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password and new_password == confirm_password:
            user_to_reset.set_password(new_password)
            user_to_reset.save()
            
            # Log the action
            AdminLog.objects.create(
                admin=admin_user,
                action='password_reset',
                target_user=user_to_reset,
                description=f"Password reset for {user_to_reset.email}",
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f"Password reset successfully for {user_to_reset.email}")
        else:
            messages.error(request, "Passwords do not match or are empty")
    
    return redirect('admin_user_management')

@login_required
@user_passes_test(is_admin)
def admin_system_reports(request):
    """Admin system reports and analytics"""
    user = request.user
    
    # School-wide statistics
    total_users = User.objects.filter(school=user.school).count()
    teachers_count = User.objects.filter(school=user.school, role='Teacher').count()
    dept_heads_count = User.objects.filter(school=user.school, role='Department Head').count()
    student_teachers_count = User.objects.filter(school=user.school, role='Student Teacher').count()
    
    # Lesson plan statistics
    total_lessons = LessonPlan.objects.filter(created_by__school=user.school).count()
    approved_lessons = LessonPlan.objects.filter(created_by__school=user.school, status='final').count()
    draft_lessons = LessonPlan.objects.filter(created_by__school=user.school, status='draft').count()
    
    # Recent admin activities
    recent_logs = AdminLog.objects.filter(admin=user).select_related('target_user').order_by('-timestamp')[:10]
    
    context = {
        'total_users': total_users,
        'teachers_count': teachers_count,
        'dept_heads_count': dept_heads_count,
        'student_teachers_count': student_teachers_count,
        'total_lessons': total_lessons,
        'approved_lessons': approved_lessons,
        'draft_lessons': draft_lessons,
        'recent_logs': recent_logs,
        'user_school': user.school,
    }
    
    return render(request, 'admin/admin_system_reports.html', context)

@login_required
@user_passes_test(is_admin)
def admin_lesson_monitoring(request):
    """Admin view all lesson plans in their school"""
    user = request.user
    
    lesson_plans = LessonPlan.objects.filter(
        created_by__school=user.school
    ).select_related('created_by').order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        lesson_plans = lesson_plans.filter(status=status_filter)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        lesson_plans = lesson_plans.filter(
            Q(title__icontains=search_query) |
            Q(created_by__first_name__icontains=search_query) |
            Q(created_by__last_name__icontains=search_query)
        )
    
    context = {
        'lesson_plans': lesson_plans,
        'total_lessons': lesson_plans.count(),
        'user_school': user.school,
    }
    
    return render(request, 'admin/admin_lesson_monitoring.html', context)

@login_required
@user_passes_test(is_admin)
def admin_export_reports(request, format_type):
    """Export reports in CSV or PDF"""
    user = request.user
    
    if format_type not in ['csv', 'pdf']:
        messages.error(request, "Invalid export format")
        return redirect('admin_system_reports')
    
    # Get users data
    users = User.objects.filter(school=user.school).order_by('role', 'last_name')
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{user.school.school_name}_users_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Name', 'Email', 'Role', 'Department', 'Status', 'Last Login'])
        
        for user_obj in users:
            writer.writerow([
                user_obj.full_name,
                user_obj.email,
                user_obj.role,
                user_obj.department,
                'Active' if user_obj.is_active else 'Inactive',
                user_obj.last_login.strftime('%Y-%m-%d %H:%M') if user_obj.last_login else 'Never'
            ])
        
        return response
    
    elif format_type == 'pdf':
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        
        # Title
        title = Paragraph(f"User Report - {user.school.school_name}", title_style)
        elements.append(title)
        
        # Table data
        data = [['Name', 'Email', 'Role', 'Department', 'Status']]
        for user_obj in users:
            data.append([
                user_obj.full_name,
                user_obj.email,
                user_obj.role,
                user_obj.department,
                'Active' if user_obj.is_active else 'Inactive'
            ])
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{user.school.school_name}_users_report.pdf"'
        
        return response