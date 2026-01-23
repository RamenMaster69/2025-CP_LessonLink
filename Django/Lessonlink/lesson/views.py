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
from django.utils import timezone
from .models import LessonPlanSubmission, User, Schedule, Task, TaskNotification, SchoolRegistration, AdminLog, Exemplar, StudentConcern
from lessonGenerator.models import LessonPlan
from .serializers import ScheduleSerializer, ExemplarSerializer
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
from .forms import SchoolAdminRegistrationForm
logger = logging.getLogger(__name__)
from lessonlinkNotif.models import Notification
from django.http import HttpResponseForbidden
from functools import wraps
import PyPDF2
from docx import Document
import mammoth
import tempfile
from django.views.decorators.http import require_POST, require_http_methods

# School Registration Views
from django.contrib.auth.hashers import make_password

def org_reg_1(request):
    """Handle school registration form - both GET and POST"""
    
    print("\n" + "="*60)
    print("DEBUG: org_reg_1 VIEW CALLED")
    print(f"DEBUG: Request method: {request.method}")
    print(f"DEBUG: Path: {request.path}")
    print("="*60)
    
    if request.method == 'GET':
        print("DEBUG: GET request - rendering form")
        # Prepare provinces and regions for template
        regions = [
            'NCR - National Capital Region',
            'Region I - Ilocos Region',
            'Region II - Cagayan Valley',
            'Region III - Central Luzon',
            'Region IV-A - CALABARZON',
            'Region IV-B - MIMAROPA',
            'Region V - Bicol Region',
            'Region VI - Western Visayas',
            'Region VII - Central Visayas',
            'Region VIII - Eastern Visayas',
            'Region IX - Zamboanga Peninsula',
            'Region X - Northern Mindanao',
            'Region XI - Davao Region',
            'Region XII - SOCCSKSARGEN',
            'Region XIII - Caraga',
            'BARMM - Bangsamoro Autonomous Region in Muslim Mindanao',
            'CAR - Cordillera Administrative Region',
        ]
        
        # Prepare provinces by region for JavaScript filtering
        provinces_by_region = {
            'NCR - National Capital Region': [
                'Caloocan (NCR)', 'Las Piñas (NCR)', 'Makati (NCR)', 'Malabon (NCR)', 'Mandaluyong (NCR)',
                'Manila (NCR)', 'Marikina (NCR)', 'Muntinlupa (NCR)', 'Navotas (NCR)', 'Parañaque (NCR)',
                'Pasay (NCR)', 'Pasig (NCR)', 'Quezon City (NCR)', 'San Juan (NCR)', 'Taguig (NCR)', 
                'Valenzuela (NCR)', 'Pateros (NCR)'
            ],
            'Region I - Ilocos Region': [
                'Ilocos Norte', 'Ilocos Sur', 'La Union', 'Pangasinan'
            ],
            'CAR - Cordillera Administrative Region': [
                'Abra', 'Apayao', 'Benguet', 'Ifugao', 'Kalinga', 'Mountain Province'
            ],
            'Region II - Cagayan Valley': [
                'Batanes', 'Cagayan', 'Isabela', 'Nueva Vizcaya', 'Quirino'
            ],
            'Region III - Central Luzon': [
                'Aurora', 'Bataan', 'Bulacan', 'Nueva Ecija', 'Pampanga',
                'Tarlac', 'Zambales'
            ],
            'Region IV-A - CALABARZON': [
                'Batangas', 'Cavite', 'Laguna', 'Quezon', 'Rizal'
            ],
            'Region IV-B - MIMAROPA': [
                'Marinduque', 'Occidental Mindoro', 'Oriental Mindoro',
                'Palawan', 'Romblon'
            ],
            'Region V - Bicol Region': [
                'Albay', 'Camarines Norte', 'Camarines Sur', 'Catanduanes',
                'Masbate', 'Sorsogon'
            ],
            'Region VI - Western Visayas': [
                'Aklan', 'Antique', 'Capiz', 'Guimaras', 'Iloilo', 'Negros Occidental'
            ],
            'Region VII - Central Visayas': [
                'Bohol', 'Cebu', 'Negros Oriental', 'Siquijor'
            ],
            'Region VIII - Eastern Visayas': [
                'Biliran', 'Eastern Samar', 'Leyte', 'Northern Samar', 'Samar', 'Southern Leyte'
            ],
            'Region IX - Zamboanga Peninsula': [
                'Zamboanga del Norte', 'Zamboanga del Sur', 'Zamboanga Sibugay'
            ],
            'Region X - Northern Mindanao': [
                'Bukidnon', 'Camiguin', 'Lanao del Norte', 'Misamis Occidental', 'Misamis Oriental'
            ],
            'Region XI - Davao Region': [
                'Davao de Oro', 'Davao del Norte', 'Davao del Sur', 'Davao Occidental', 'Davao Oriental'
            ],
            'Region XII - SOCCSKSARGEN': [
                'Cotabato', 'Sarangani', 'South Cotabato', 'Sultan Kudarat'
            ],
            'Region XIII - Caraga': [
                'Agusan del Norte', 'Agusan del Sur', 'Dinagat Islands', 'Surigao del Norte', 'Surigao del Sur'
            ],
            'BARMM - Bangsamoro Autonomous Region in Muslim Mindanao': [
                'Basilan', 'Lanao del Sur', 'Maguindanao del Norte', 'Maguindanao del Sur', 'Sulu', 'Tawi-Tawi'
            ],
        }
        
        context = {
            'regions_json': json.dumps(list(provinces_by_region.keys())),
            'provinces_by_region_json': json.dumps(provinces_by_region),
            'all_provinces_json': json.dumps([prov for region_provinces in provinces_by_region.values() for prov in region_provinces]),
        }
        return render(request, 'org_reg/org_reg_1.html', context)
    
    elif request.method == 'POST':
        print("\n" + "="*60)
        print("DEBUG: POST REQUEST RECEIVED!")
        print("="*60)
        
        # DEBUG: Check if form is actually submitting
        print("🔍 CHECKING FORM DATA:")
        print(f"  CSRF token present: {'csrfmiddlewaretoken' in request.POST}")
        print(f"  Password field in POST: {'password' in request.POST}")
        print(f"  Password value: {request.POST.get('password')}")
        
        # List all POST data for debugging
        print("\n📦 ALL POST DATA KEYS:")
        for key in request.POST.keys():
            value = request.POST.get(key)
            print(f"  {key}: {value}")
        
        # List all FILES data for debugging
        print("\n📁 ALL FILES DATA:")
        for key in request.FILES.keys():
            file = request.FILES[key]
            print(f"  {key}: {file.name} ({file.size} bytes)")
        
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
                'password': request.POST.get('password', '').strip(),
                'accuracy': request.POST.get('accuracy') == 'on',
                'terms': request.POST.get('terms') == 'on',
                'communications': request.POST.get('communications') == 'on',
            }

            # Debug the extracted data
            print("\n📊 EXTRACTED FORM DATA:")
            for key, value in form_data.items():
                print(f"  {key}: {value}")
            print("="*60)
            
            # Validate required fields
            required_fields = [
                'school_name', 'school_id', 'address', 'province', 'region',
                'phone_number', 'email', 'contact_person', 'position',
                'contact_email', 'contact_phone', 'password'
            ]
            
            missing_fields = []
            for field in required_fields:
                if not form_data[field]:
                    missing_fields.append(field.replace('_', ' ').title())
            
            if missing_fields:
                print(f"❌ MISSING FIELDS: {missing_fields}")
                messages.error(request, f"Please complete the following required fields: {', '.join(missing_fields)}")
                return render(request, 'org_reg/org_reg_1.html', {'form_data': form_data})
            
            # Validate password strength
            password = form_data['password']
            if len(password) < 8:
                print(f"❌ PASSWORD TOO SHORT: {len(password)} chars")
                messages.error(request, "Password must be at least 8 characters long.")
                return render(request, 'org_reg/org_reg_1.html', {'form_data': form_data})
            
            # Check if school_id already exists
            if SchoolRegistration.objects.filter(school_id=form_data['school_id']).exists():
                print(f"❌ SCHOOL ID ALREADY EXISTS: {form_data['school_id']}")
                messages.error(request, f"A school with ID '{form_data['school_id']}' is already registered.")
                return render(request, 'org_reg/org_reg_1.html', {'form_data': form_data})
            
            # Check if email already exists in User model
            if User.objects.filter(email=form_data['contact_email']).exists():
                print(f"❌ USER EMAIL ALREADY EXISTS: {form_data['contact_email']}")
                messages.error(request, f"An account with email '{form_data['contact_email']}' already exists.")
                return render(request, 'org_reg/org_reg_1.html', {'form_data': form_data})
            
            # Handle file upload for school logo
            school_logo = None
            if 'school_logo' in request.FILES:
                logo_file = request.FILES['school_logo']
                print(f"📸 LOGO FILE DETECTED: {logo_file.name} ({logo_file.size} bytes)")
                
                # Validate file type
                allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
                if logo_file.content_type not in allowed_types:
                    print(f"❌ INVALID LOGO TYPE: {logo_file.content_type}")
                    messages.error(request, "Invalid logo file type. Please upload JPG, PNG, GIF, or WebP.")
                    return render(request, 'org_reg/org_reg_1.html', {'form_data': form_data})
                
                # Validate file size (max 2MB)
                if logo_file.size > 2 * 1024 * 1024:
                    print(f"❌ LOGO TOO LARGE: {logo_file.size} bytes")
                    messages.error(request, "Logo file is too large. Maximum size is 2MB.")
                    return render(request, 'org_reg/org_reg_1.html', {'form_data': form_data})
                
                school_logo = logo_file
                print("✅ LOGO VALIDATION PASSED")
            
            print("\n🏫 ATTEMPTING TO CREATE SCHOOL REGISTRATION...")
            
            # Create the school registration record
            school_registration = SchoolRegistration(
                school_name=form_data['school_name'],
                school_id=form_data['school_id'],
                year_established=form_data['year_established'] or None,
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
                password_hash=make_password(form_data['password']),  # Store hashed password
                accuracy=form_data['accuracy'],
                terms=form_data['terms'],
                communications=form_data['communications'],
                status='pending'
            )
            
            print("✅ SCHOOL REGISTRATION OBJECT CREATED")
            print(f"  School Name: {school_registration.school_name}")
            print(f"  School ID: {school_registration.school_id}")
            print(f"  Contact Email: {school_registration.contact_email}")
            
            try:
                # Save the school registration first
                print("💾 ATTEMPTING TO SAVE TO DATABASE...")
                school_registration.save()
                print(f"✅ SCHOOL REGISTRATION SAVED! ID: {school_registration.id}")
                print(f"✅ Database entry created at: {school_registration.created_at}")
                
            except Exception as save_error:
                print(f"❌ DATABASE SAVE ERROR: {str(save_error)}")
                print(f"❌ Error type: {type(save_error)}")
                import traceback
                print(f"❌ Traceback:\n{traceback.format_exc()}")
                messages.error(request, f"Database error: {str(save_error)}")
                return render(request, 'org_reg/org_reg_1.html', {'form_data': form_data})
            
            # Handle logo upload after saving
            if school_logo:
                print("🖼️ PROCESSING LOGO UPLOAD...")
                try:
                    # Generate unique filename
                    import time
                    timestamp = int(time.time())
                    file_extension = logo_file.name.split('.')[-1].lower()
                    filename = f"school_logos/{school_registration.school_id}_{timestamp}.{file_extension}"
                    
                    # Save the file
                    path = default_storage.save(filename, logo_file)
                    school_registration.school_logo = path
                    school_registration.logo_filename = logo_file.name
                    school_registration.save()
                    print(f"✅ LOGO SAVED: {path}")
                except Exception as logo_error:
                    print(f"⚠️ LOGO UPLOAD ERROR (continuing anyway): {str(logo_error)}")
            
            # Create a user account for the school admin (inactive until approved)
            print("\n👤 CREATING USER ACCOUNT...")
            try:
                # Split contact person name into first and last name
                name_parts = form_data['contact_person'].split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else "Admin"
                
                print(f"  First Name: {first_name}")
                print(f"  Last Name: {last_name}")
                print(f"  Email: {form_data['contact_email']}")
                print(f"  Password provided: {'Yes' if form_data['password'] else 'No'}")
                
                # Create user account but keep it inactive until school is approved
                user = User.objects.create_user(
                    email=form_data['contact_email'],
                    password=form_data['password'],  # Raw password for initial login
                    first_name=first_name,
                    last_name=last_name,
                    role='Admin',
                    rank=form_data['position'],
                    department='Administration',
                    school=school_registration,
                    is_active=False  # Inactive until school is approved
                )
                
                print(f"✅ USER ACCOUNT CREATED! ID: {user.id}")
                
                # Log both creations
                logger.info(f"New school registration: {school_registration.school_name} ({school_registration.school_id})")
                logger.info(f"Created user account: {user.email} for school {school_registration.school_name}")
                
            except Exception as user_error:
                print(f"❌ USER CREATION ERROR: {str(user_error)}")
                import traceback
                print(f"❌ Traceback:\n{traceback.format_exc()}")
                
                # If user creation fails, delete the school registration and show error
                try:
                    school_registration.delete()
                    print("⚠️ Deleted school registration due to user creation failure")
                except:
                    pass
                    
                messages.error(request, f"Failed to create user account: {str(user_error)}")
                return render(request, 'org_reg/org_reg_1.html', {'form_data': form_data})
            
            # Final success check
            print("\n" + "="*60)
            print("✅✅✅ REGISTRATION SUCCESSFUL! ✅✅✅")
            print(f"  School: {school_registration.school_name}")
            print(f"  School ID: {school_registration.school_id}")
            print(f"  Admin Email: {school_registration.contact_email}")
            print(f"  Registration ID: {school_registration.id}")
            print(f"  Created at: {school_registration.created_at}")
            print("="*60)
            
            # Verify it's actually in the database
            try:
                db_check = SchoolRegistration.objects.get(id=school_registration.id)
                print(f"✅ DATABASE VERIFICATION: Found school with ID {db_check.id}")
            except SchoolRegistration.DoesNotExist:
                print("❌ DATABASE VERIFICATION FAILED: School not found in database!")
            except Exception as db_error:
                print(f"❌ DATABASE VERIFICATION ERROR: {str(db_error)}")
            
            # Success message
            messages.success(
                request, 
                f"""🎉 Registration submitted successfully! 
                
                Your application for **{school_registration.school_name}** has been received and is pending review.
                
                📧 **Admin Account Created:**
                - Username/Email: {school_registration.contact_email}
                - Password: The password you created
                
                ⏳ **What happens next:**
                1. Our team will review your registration within 3-5 business days
                2. You'll receive an email notification once approved
                3. Your admin account will be activated automatically
                
                📞 **Need help?**
                - Email: lessonlink69@gmail.com
                - Phone: +63 953 866 7613
                
                Thank you for choosing LessonLink!"""
            )
            
            return redirect('landing')
            
        except ValidationError as e:
            print(f"❌ VALIDATION ERROR: {str(e)}")
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
            print(f"❌ UNEXPECTED ERROR: {str(e)}")
            import traceback
            print(f"❌ Traceback:\n{traceback.format_exc()}")
            
            # Handle unexpected errors
            logger.error(f"Error processing school registration: {str(e)}")
            messages.error(request, f"An unexpected error occurred: {str(e)}")
            return render(request, 'org_reg/org_reg_1.html', {'form_data': request.POST})



# AJAX endpoint for real-time school ID validation
@csrf_exempt
@require_POST
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


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_teachers_by_department(request):
    """API endpoint to get teachers by school and department"""
    school_id = request.GET.get('school')
    department = request.GET.get('department')
    
    if not school_id or not department:
        return JsonResponse({'teachers': []})
    
    try:
        # Get teachers from the same school and department
        teachers = User.objects.filter(
            role='Teacher',
            school_id=school_id,
            department=department,
            is_active=True
        ).values('id', 'first_name', 'last_name', 'email')
        
        return JsonResponse({'teachers': list(teachers)})
    
    except Exception as e:
        logger.error(f"Error fetching teachers: {str(e)}")
        return JsonResponse({'teachers': []})


# Rest of your views remain the same...
# Only showing the school registration related views above
# The rest of your views (login, dashboard, etc.) should remain as they were

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
                file_extension = 'jpg'
            
            import time
            timestamp = int(time.time())
            filename = f"profile_pictures/user_{user.id}_{timestamp}.{file_extension}"
            
            # Save the file
            path = default_storage.save(filename, profile_picture)
            
            # Update user's profile picture - save the relative path
            user.profile_picture.name = path  # This should be the relative path
            user.save()
            
            # Get the absolute URL for the image
            from django.contrib.sites.shortcuts import get_current_site
            current_site = get_current_site(request)
            
            # Construct the full URL
            image_url = f"http://{current_site.domain}{settings.MEDIA_URL}{path}"
            
            # For development, you can also use relative URL
            # image_url = f"{settings.MEDIA_URL}{path}?v={timestamp}"
            
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
        assign_teacher = request.POST.get("assign_teacher")  # Get supervising teacher
        
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

        # Additional validation for Student Teachers
        if role == 'Student Teacher' and not assign_teacher:
            messages.error(request, "Please select a supervising teacher.")
            return render(request, 'registration/registration_4.html', {
                'department': department,
                'school': school_id,
                'affiliations': affiliations,
                'schools': approved_schools,
                'error_message': "Please select a supervising teacher.",
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

            # Handle supervising teacher assignment for Student Teachers
            if role == 'Student Teacher' and assign_teacher:
                try:
                    supervising_teacher = User.objects.get(
                        id=assign_teacher, 
                        role='Teacher',
                        school=school,
                        department=department
                    )
                    user.supervising_teacher = supervising_teacher
                    user.save()
                    print(f"DEBUG - Assigned supervising teacher: {supervising_teacher.email}")
                except User.DoesNotExist:
                    messages.error(request, "Selected teacher not found. Please try again.")
                    return render(request, 'registration/registration_4.html', {
                        'department': department,
                        'school': school_id,
                        'affiliations': affiliations,
                        'schools': approved_schools,
                        'error_message': "Selected teacher not found. Please try again.",
                        'show_error': True
                    })

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


@login_required
def teacher_student_list(request):
    """Teacher's view of all their supervised students in a table format"""
    if request.user.role != 'Teacher':
        messages.error(request, "You are not authorized to access this page.")
        return redirect('dashboard')
    
    # Get all supervised students
    supervised_students = User.objects.filter(
        supervising_teacher=request.user,
        is_active=True
    ).select_related('school').order_by('first_name', 'last_name')
    
    # Add lesson plan counts for each student
    from lessonGenerator.models import LessonPlan
    from django.db.models import Count, Q
    
    for student in supervised_students:
        student.lesson_plans_count = LessonPlan.objects.filter(created_by=student).count()
        student.completed_lessons_count = LessonPlan.objects.filter(
            created_by=student, 
            status='final'
        ).count()
        
        # ADD CONCERNS COUNT
        student.pending_concerns_count = StudentConcern.objects.filter(
            student=student,
            status='pending'
        ).count()
        student.has_pending_concerns = student.pending_concerns_count > 0
    
    # Get statistics for the page
    total_completed_lessons = LessonPlan.objects.filter(
        created_by__supervising_teacher=request.user,
        status='final'
    ).count()
    
    # Count pending reviews for this teacher's students
    from .models import LessonPlanSubmission
    pending_reviews = LessonPlanSubmission.objects.filter(
        submitted_by__supervising_teacher=request.user,
        status='submitted'
    ).count()
    
    # ADD STUDENT CONCERNS COUNT
    student_concerns_count = StudentConcern.objects.filter(
        student__supervising_teacher=request.user,
        status='pending'
    ).count()
    
    # Get recent student concerns for the concerns section
    student_concerns = StudentConcern.objects.filter(
        student__supervising_teacher=request.user
    ).select_related('student').order_by('-created_at')[:10]
    
    context = {
        'supervised_students': supervised_students,
        'total_completed_lessons': total_completed_lessons,
        'pending_reviews': pending_reviews,
        'student_concerns_count': student_concerns_count,  # ADD THIS
        'student_concerns': student_concerns,  # ADD THIS
        'user': request.user
    }
    
    return render(request, 'teacher/student_list.html', context)




@login_required
def teacher_student_detail(request, student_id):
    """Teacher's view of a specific student's details"""
    if request.user.role != 'Teacher':
        messages.error(request, "You are not authorized to access this page.")
        return redirect('dashboard')
    
    student = get_object_or_404(User, 
        id=student_id, 
        supervising_teacher=request.user,
        is_active=True
    )
    
    # Get student's lesson plans
    from lessonGenerator.models import LessonPlan
    student_lesson_plans = LessonPlan.objects.filter(
        created_by=student
    ).order_by('-created_at')
    
    context = {
        'student': student,
        'lesson_plans': student_lesson_plans,
        'user': request.user
    }
    
    return render(request, 'teacher/student_detail.html', context)




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
            if check_password(password, school_reg.password_hash):
                # Find or create user account for this school admin
                user, created = User.objects.get_or_create(
                    email=school_reg.contact_email,  # Use contact_email as primary email
                    defaults={
                        'first_name': school_reg.contact_person.split(' ', 1)[0] if ' ' in school_reg.contact_person else school_reg.contact_person,
                        'last_name': school_reg.contact_person.split(' ', 1)[1] if ' ' in school_reg.contact_person else 'Admin',
                        'role': 'Admin',
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
            if check_password(password, school_reg.password_hash):
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
                        role='Admin',
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
    
    # Get supervised students for teachers - ADD THIS SECTION
    supervised_students = []
    if user.role == 'Teacher':
        supervised_students = User.objects.filter(
            supervising_teacher=user,
            is_active=True,
            role='Student Teacher'
        ).select_related('school').order_by('first_name', 'last_name')
        
        # DEBUG: Print to console to verify
        print(f"DEBUG: Teacher {user.email} has {supervised_students.count()} students")
        for student in supervised_students:
            print(f"DEBUG: Student - {student.email}")
    
    # FIXED: Use timezone-aware today calculation
    from django.utils import timezone
    
    today = timezone.localtime(timezone.now()).strftime('%A').lower()
    todays_schedule = Schedule.objects.filter(user=user, day=today).order_by('time')
    
    return render(request, 'dashboard.html', {
        'user': user,
        'full_name': user.full_name,
        'total_tasks': total_tasks,
        'total_lesson_plans': total_lesson_plans,
        'draft_lesson_plans': draft_lesson_plans,
        'recent_lesson_plans': recent_lesson_plans,
        'todays_schedule': todays_schedule,
        'today_display': timezone.localtime(timezone.now()).strftime('%A'),  # For display
        'supervised_students': supervised_students,  # ADD THIS LINE
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
@require_POST
def update_student_approval(request, student_id):
    """Update student approval status - for teachers only"""
    print(f"DEBUG: Approval update called for student {student_id} by user {request.user.email}")
    
    if request.user.role != 'Teacher':
        return JsonResponse({'success': False, 'error': 'Unauthorized - Teachers only'}, status=403)
    
    try:
        student = User.objects.get(
            id=student_id, 
            supervising_teacher=request.user,
            is_active=True
        )
        print(f"DEBUG: Found student: {student.email}")
        
        # Get the raw request body to debug
        raw_body = request.body.decode('utf-8')
        print(f"DEBUG: Raw request body: {raw_body}")
        
        # Parse JSON data
        try:
            data = json.loads(raw_body)
            approval_status = data.get('approval_status')
            rejection_reason = data.get('rejection_reason', '')
            print(f"DEBUG: Parsed approval_status: {approval_status}")
            print(f"DEBUG: Parsed rejection_reason: {rejection_reason}")
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON decode error: {e}")
            return JsonResponse({'success': False, 'error': f'Invalid JSON data: {str(e)}'})
        
        # Validate the status
        valid_statuses = ['approved', 'disapproved', 'pending']
        if approval_status not in valid_statuses:
            print(f"DEBUG: Invalid status received: {approval_status}. Valid statuses: {valid_statuses}")
            return JsonResponse({
                'success': False, 
                'error': f'Invalid status: {approval_status}. Must be one of: {", ".join(valid_statuses)}'
            })
        
        # Validate rejection reason for disapproval
        if approval_status == 'disapproved' and not rejection_reason:
            print(f"DEBUG: Rejection reason required for disapproval")
            return JsonResponse({
                'success': False, 
                'error': 'Rejection reason is required when disapproving a student'
            })
        
        # Update the student
        print(f"DEBUG: Updating student {student.email} status from {student.approval_status} to {approval_status}")
        student.approval_status = approval_status
        
        # Store rejection reason if provided
        if approval_status == 'disapproved' and rejection_reason:
            print(f"DEBUG: Storing rejection reason: {rejection_reason}")
            student.rejection_reason = rejection_reason
        elif approval_status == 'approved':
            # Clear rejection reason if approving
            student.rejection_reason = ''
        
        student.save()
        
        # TODO: Send notification to student about the status change
        # If rejected, include the rejection reason
        if approval_status == 'disapproved' and rejection_reason:
            # You can add notification logic here
            print(f"DEBUG: Student {student.email} rejected with reason: {rejection_reason}")
        
        print(f"DEBUG: Successfully updated approval status")
        return JsonResponse({'success': True})
            
    except User.DoesNotExist:
        print(f"DEBUG: Student {student_id} not found or not supervised by this teacher")
        return JsonResponse({'success': False, 'error': 'Student not found or you are not their supervising teacher'})
    except Exception as e:
        logger.error(f"Error updating student approval: {str(e)}")
        print(f"DEBUG: Unexpected error: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})


        





@require_POST
@csrf_exempt
@login_required
def submit_student_concern(request):
    """Handle student concern submission"""
    try:
        data = json.loads(request.body)
        
        # Create the concern
        concern = StudentConcern.objects.create(
            student=request.user,
            subject=data.get('subject'),
            concern_type=data.get('concern_type'),
            content=data.get('content'),
            status='pending'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Concern submitted successfully',
            'concern_id': concern.id
        })
        
    except Exception as e:
        logger.error(f"Error submitting student concern: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)






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
def get_student_concerns(request, student_id):
    """Get concerns for a specific student"""
    if request.user.role != 'Teacher':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    try:
        student = User.objects.get(id=student_id, supervising_teacher=request.user)
        concerns = StudentConcern.objects.filter(student=student).order_by('-created_at')
        
        concerns_data = []
        for concern in concerns:
            concerns_data.append({
                'id': concern.id,
                'subject': concern.subject,
                'concern_type': concern.concern_type,
                'content': concern.content,
                'status': concern.status,
                'created_at': concern.created_at.strftime('%Y-%m-%d %H:%M'),
                'rejection_reason': concern.rejection_reason
            })
        
        return JsonResponse({'success': True, 'concerns': concerns_data})
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
@login_required
def resolve_student_concern(request, concern_id):
    """Mark a concern as resolved"""
    if request.user.role != 'Teacher':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    try:
        concern = StudentConcern.objects.get(id=concern_id, student__supervising_teacher=request.user)
        concern.status = 'resolved'
        concern.save()
        
        return JsonResponse({'success': True, 'message': 'Concern marked as resolved'})
        
    except StudentConcern.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Concern not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


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
            school.processed_at = timezone.now()
            school.processed_by = request.user
            school.save()
            
            # Activate the school admin user
            admin_user = User.objects.filter(
                email=school.contact_email,
                school=school
            ).first()
            
            if admin_user:
                admin_user.is_active = True
                admin_user.save()
            
            # Log the action
            AdminLog.objects.create(
                admin=request.user,
                action='school_approved',
                target_school=school,
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
            reason = request.POST.get('reason', 'No reason provided')
            
            school.status = 'rejected'
            school.admin_notes = reason
            school.processed_at = timezone.now()
            school.processed_by = request.user
            school.save()
            
            # Log the action
            AdminLog.objects.create(
                admin=request.user,
                action='school_rejected',
                target_school=school,
                description=f"Rejected school: {school.school_name} (ID: {school.school_id}). Reason: {reason}",
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
    
    # Get admin actions related to this school
    admin_logs = AdminLog.objects.filter(target_school=school).order_by('-timestamp')[:10]
    
    context = {
        'school': school,
        'school_users': school_users,
        'users_count': school_users.count(),
        'admin_logs': admin_logs,
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

def Dep_exemplar(request):
    return render(request, "Dep_exemplar.html")

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
    
    # Get lesson plan statistics for dashboard - SAME AS DASHBOARD
    from lessonGenerator.models import LessonPlan
    
    # Total Lesson Plans (all lesson plans for the user)
    total_lesson_plans = LessonPlan.objects.filter(created_by=user).count()
    
    # Draft Lesson Plans (only those with draft status)
    draft_lesson_plans = LessonPlan.objects.filter(created_by=user, status='draft').count()
    
    # Get task statistics for dashboard
    total_tasks = Task.objects.filter(user=user).count()
    
    # Get recent lesson plans (5 most recent)
    recent_lesson_plans = LessonPlan.objects.filter(created_by=user).order_by('-created_at')[:5]
    
    # Get today's schedule - SAME AS DASHBOARD
    from django.utils import timezone
    import pytz
    
    today = timezone.localtime(timezone.now()).strftime('%A').lower()
    todays_schedule = Schedule.objects.filter(user=user, day=today).order_by('time')
    
    return render(request, 'st_dash.html', {
        'user': user,
        'full_name': user.full_name,
        'total_tasks': total_tasks,
        'total_lesson_plans': total_lesson_plans,
        'draft_lesson_plans': draft_lesson_plans,
        'recent_lesson_plans': recent_lesson_plans,
        'todays_schedule': todays_schedule,
        'today_display': timezone.localtime(timezone.now()).strftime('%A')  # For display
    })

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
    """Submit a lesson plan for approval - handles both department head and supervising teacher workflows"""
    if request.method == 'POST':
        try:
            # Get the lesson plan
            lesson_plan = LessonPlan.objects.get(id=lesson_plan_id, created_by=request.user)
            
            # Validate that the user has the required school and department information
            if not request.user.school:
                messages.error(request, "You are not assigned to any school. Please contact administrator.")
                return redirect('draft_list')
            
            # ==================== STUDENT TEACHER WORKFLOW ====================
            if request.user.role == "Student Teacher":
                if not request.user.supervising_teacher:
                    messages.error(request, "You don't have a supervising teacher assigned. Please contact administrator.")
                    return redirect('draft_list')
                
                if not request.user.department:
                    messages.error(request, "You are not assigned to any department. Please contact administrator.")
                    return redirect('draft_list')
                
                # Validate that student teacher and supervising teacher are in same school and department
                if (request.user.school != request.user.supervising_teacher.school or 
                    request.user.department != request.user.supervising_teacher.department):
                    messages.error(request, 
                        f"Your supervising teacher {request.user.supervising_teacher.full_name} is not in your school/department. "
                        "Please contact administrator."
                    )
                    return redirect('draft_list')
                
                # Check if already submitted to supervising teacher
                existing_submission = LessonPlanSubmission.objects.filter(
                    lesson_plan=lesson_plan,
                    submitted_to=request.user.supervising_teacher,
                    status__in=['submitted', 'approved', 'needs_revision']
                ).first()
                
                if existing_submission:
                    status_display = existing_submission.get_status_display()
                    messages.warning(request, 
                        f"This lesson plan has already been submitted to your supervising teacher. "
                        f"Current status: {status_display}"
                    )
                    return redirect('draft_list')
                
                # Create submission to supervising teacher
                submission = LessonPlanSubmission.objects.create(
                    lesson_plan=lesson_plan,
                    submitted_by=request.user,
                    submitted_to=request.user.supervising_teacher,
                    status='submitted'
                )
                
                # Update lesson plan status to final when submitted
                lesson_plan.status = LessonPlan.FINAL
                lesson_plan.save()
                
                # Create submission notification for supervising teacher
                from lessonlinkNotif.models import Notification
                Notification.create_lesson_submitted_notification(submission)
                
                messages.success(request, 
                    f"Lesson plan submitted successfully to your supervising teacher: "
                    f"{request.user.supervising_teacher.full_name}! "
                    f"They will review your lesson plan and provide feedback."
                )
                
                # Log the submission
                logger.info(f"Student Teacher {request.user.email} submitted lesson plan {lesson_plan.id} to supervising teacher {request.user.supervising_teacher.email}")
            
            # ==================== TEACHER WORKFLOW (to Department Head) ====================
            elif request.user.role == "Teacher":
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
                    messages.error(request, 
                        f"No active Department Head found for {request.user.department} department in {request.user.school}. "
                        "Please contact administrator."
                    )
                    return redirect('draft_list')
                
                # Check if already submitted to department head
                existing_submission = LessonPlanSubmission.objects.filter(
                    lesson_plan=lesson_plan,
                    submitted_to=department_head,
                    status__in=['submitted', 'approved', 'needs_revision']
                ).first()
                
                if existing_submission:
                    status_display = existing_submission.get_status_display()
                    messages.warning(request, 
                        f"This lesson plan has already been submitted to the department head. "
                        f"Current status: {status_display}"
                    )
                    return redirect('draft_list')
                
                # Create submission to department head
                submission = LessonPlanSubmission.objects.create(
                    lesson_plan=lesson_plan,
                    submitted_by=request.user,
                    submitted_to=department_head,
                    status='submitted'
                )
                
                # Update lesson plan status to final when submitted
                lesson_plan.status = LessonPlan.FINAL
                lesson_plan.save()
                
                # Create submission notification for department head
                from lessonlinkNotif.models import Notification
                Notification.create_lesson_submitted_notification(submission)
                
                messages.success(request, 
                    f"Lesson plan submitted successfully to department head: "
                    f"{department_head.full_name}! "
                    f"They will review your lesson plan and provide feedback."
                )
                
                # Log the submission
                logger.info(f"Teacher {request.user.email} submitted lesson plan {lesson_plan.id} to department head {department_head.email}")
            
            # ==================== DEPARTMENT HEAD WORKFLOW (Auto-approval) ====================
            elif request.user.role == "Department Head":
                # Department heads can auto-approve their own lesson plans
                lesson_plan.status = LessonPlan.FINAL
                lesson_plan.auto_approved = True
                lesson_plan.save()
                
                messages.success(request, 
                    "Lesson plan automatically approved! "
                    "As a Department Head, your lesson plans are approved immediately."
                )
                
                # Log the auto-approval
                logger.info(f"Department Head {request.user.email} auto-approved their lesson plan {lesson_plan.id}")
            
            # ==================== OTHER ROLES ====================
            else:
                messages.error(request, 
                    f"Lesson plan submission is not available for your role ({request.user.role}). "
                    "Please contact administrator."
                )
                return redirect('draft_list')
                
        except LessonPlan.DoesNotExist:
            messages.error(request, "Lesson plan not found or you don't have permission to submit it.")
        except Exception as e:
            logger.error(f"Error submitting lesson plan {lesson_plan_id}: {str(e)}")
            messages.error(request, f"An error occurred while submitting the lesson plan: {str(e)}")
        
        return redirect('draft_list')
    
    # If not POST request, redirect to dashboard
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
    """Review a lesson plan submission - works for both department heads and supervising teachers"""
    if request.method == 'POST':
        try:
            submission = LessonPlanSubmission.objects.get(id=submission_id)
            
            # Check if user has permission to review this submission
            if submission.submitted_to != request.user:
                messages.error(request, "You are not authorized to review this lesson plan.")
                return redirect('dashboard')
            
            action = request.POST.get('action')
            review_notes = request.POST.get('review_notes', '').strip()
            
            if action == 'approve':
                submission.status = 'approved'
                submission.lesson_plan.status = LessonPlan.FINAL
                
                # Create approval notification
                try:
                    from lessonlinkNotif.models import Notification
                    Notification.create_draft_status_notification(submission, approved=True)
                except Exception as e:
                    print(f"Notification creation error: {e}")
                    # Continue even if notification fails
                
                messages.success(request, f"Lesson plan '{submission.lesson_plan.title}' approved successfully!")
                
            elif action == 'reject':
                submission.status = 'rejected'
                
                # Change lesson plan back to draft so it can be revised
                submission.lesson_plan.status = LessonPlan.DRAFT
                submission.lesson_plan.save()
                
                # Create rejection notification
                try:
                    from lessonlinkNotif.models import Notification
                    Notification.create_draft_status_notification(submission, approved=False)
                except Exception as e:
                    print(f"Notification creation error: {e}")
                    # Continue even if notification fails
                
                messages.success(request, f"Lesson plan '{submission.lesson_plan.title}' rejected.")
                
            elif action == 'needs_revision':
                submission.status = 'needs_revision'
                
                # Change lesson plan back to draft so it can be revised
                submission.lesson_plan.status = LessonPlan.DRAFT
                submission.lesson_plan.save()
                
                # Create needs revision notification
                try:
                    from lessonlinkNotif.models import Notification
                    Notification.create_draft_status_notification(submission, approved=False)
                except Exception as e:
                    print(f"Notification creation error: {e}")
                    # Continue even if notification fails
                
                messages.success(request, f"Lesson plan '{submission.lesson_plan.title}' returned for revision.")
            
            else:
                messages.error(request, "Invalid action specified.")
                return redirect('dashboard')
            
            submission.review_notes = review_notes
            submission.review_date = timezone.now()
            submission.save()
            
            if submission.lesson_plan.status == LessonPlan.FINAL:
                submission.lesson_plan.save()
            
            # Log the review action
            logger.info(f"{request.user.role} {request.user.email} {action} lesson plan {submission.lesson_plan.id} from {submission.submitted_by.email}")
            
        except LessonPlanSubmission.DoesNotExist:
            messages.error(request, "Submission not found.")
        except Exception as e:
            logger.error(f"Error in review_lesson_plan: {str(e)}")
            messages.error(request, f"An error occurred: {str(e)}")
        
        # Redirect based on user role
        if request.user.role == 'Teacher':
            return redirect('supervising_teacher_reviews')
        else:
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




# Add to views.py
@login_required
def get_concern_detail(request, concern_id):
    """Get detailed information about a specific concern"""
    if request.user.role != 'Teacher':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    try:
        concern = StudentConcern.objects.get(
            id=concern_id,
            student__supervising_teacher=request.user
        )
        
        concern_data = {
            'id': concern.id,
            'subject': concern.subject,
            'concern_type': concern.concern_type,
            'content': concern.content,
            'status': concern.status,
            'rejection_reason': concern.rejection_reason,
            'created_at': concern.created_at.strftime('%Y-%m-%d %H:%M'),
            'student_name': concern.student.full_name,
            'student_email': concern.student.email
        }
        
        return JsonResponse({'success': True, 'concern': concern_data})
        
    except StudentConcern.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Concern not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



        

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


@login_required
def Dep_exemplar(request):
    """Render the exemplar management page"""
    user = request.user
    
    # Only allow Department Head
    if user.role != "Department Head":
        messages.error(request, "You are not allowed to access this page.")
        return redirect("dashboard")
    
    return render(request, "Dep_exemplar.html")

@login_required
def get_department_exemplars(request):
    """Get exemplars for user's department - works for both teachers and student teachers"""
    try:
        user = request.user
        
        # For student teachers, get exemplars from their department head in the same department and school
        if user.role == 'Student Teacher':
            # Get department head for the same department and school
            department_head = User.objects.filter(
                role='Department Head',
                department=user.department,
                school=user.school,
                is_active=True
            ).first()
            
            if department_head:
                # Get exemplars uploaded by department head for this department
                exemplars = Exemplar.objects.filter(
                    user=department_head,
                    department=user.department
                ).order_by('-upload_date')
                
                serializer = ExemplarSerializer(exemplars, many=True)
                
                return JsonResponse({
                    'success': True,
                    'exemplars': serializer.data,
                    'user_role': user.role,
                    'department': user.department
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'No department head found for your department.'
                }, status=404)
        
        # For teachers, get exemplars from their department head
        elif user.role == 'Teacher':
            # Get department head for the same department and school
            department_head = User.objects.filter(
                role='Department Head',
                department=user.department,
                school=user.school,
                is_active=True
            ).first()
            
            if department_head:
                # Get exemplars uploaded by department head for this department
                exemplars = Exemplar.objects.filter(
                    user=department_head,
                    department=user.department
                ).order_by('-upload_date')
                
                serializer = ExemplarSerializer(exemplars, many=True)
                
                return JsonResponse({
                    'success': True,
                    'exemplars': serializer.data,
                    'user_role': user.role,
                    'department': user.department
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'No department head found for your department.'
                }, status=404)
        
        # For department heads, get their own exemplars
        elif user.role == 'Department Head':
            exemplars = Exemplar.objects.filter(user=user).order_by('-upload_date')
            serializer = ExemplarSerializer(exemplars, many=True)
            
            return JsonResponse({
                'success': True,
                'exemplars': serializer.data,
                'user_role': user.role,
                'department': user.department
            })
        
        else:
            return JsonResponse({
                'success': False,
                'message': 'Access denied. Teachers and Department Heads only.'
            }, status=403)
            
    except Exception as e:
        logger.error(f"Error fetching department exemplars: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': 'Error fetching exemplars'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def upload_exemplar(request):
    """Handle exemplar file upload and processing - UPDATED TO INCLUDE DEPARTMENT"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False, 
                'message': 'No file provided'
            }, status=400)
        
        file = request.FILES['file']
        user = request.user
        
        # Validate file type
        allowed_types = ['application/pdf', 'application/msword', 
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if file.content_type not in allowed_types:
            return JsonResponse({
                'success': False, 
                'message': 'Invalid file type. Please upload PDF or Word documents only.'
            }, status=400)
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            return JsonResponse({
                'success': False, 
                'message': 'File too large. Please upload files smaller than 10MB.'
            }, status=400)
        
        # Determine file type
        file_type = 'pdf' if file.content_type == 'application/pdf' else 'docx'
        
        # Extract text content
        extracted_text = extract_text_from_file(file, file_type)
        
        # Save the exemplar with department information
        exemplar = Exemplar.objects.create(
            user=user,
            name=file.name,
            file=file,
            file_type=file_type,
            file_size=file.size,
            extracted_text=extracted_text,
            department=user.department  # Add department from user
        )
        
        # Serialize the response
        serializer = ExemplarSerializer(exemplar)
        
        return JsonResponse({
            'success': True,
            'message': 'Exemplar uploaded successfully!',
            'exemplar': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error uploading exemplar: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': f'Error processing file: {str(e)}'
        }, status=500)

def extract_text_from_file(file, file_type):
    """Extract text from PDF or Word documents"""
    try:
        if file_type == 'pdf':
            return extract_text_from_pdf(file)
        else:  # Word document
            return extract_text_from_word(file)
    except Exception as e:
        logger.error(f"Error extracting text from file: {str(e)}")
        return "Text extraction failed."

def extract_text_from_pdf(file):
    """Extract text from PDF file"""
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        # Extract text using PyPDF2
        text = ""
        with open(temp_file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n\n"
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        return text.strip()
        
    except Exception as e:
        logger.error(f"PDF text extraction error: {str(e)}")
        return "PDF text extraction failed."

def extract_text_from_word(file):
    """Extract text from Word document"""
    try:
        # For .docx files using python-docx
        if file.name.endswith('.docx'):
            document = Document(file)
            text = ""
            for paragraph in document.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        
        # For .doc files, you might need additional libraries
        else:
            # Fallback: try using mammoth for both .doc and .docx
            result = mammoth.extract_raw_text(file)
            return result.value.strip()
            
    except Exception as e:
        logger.error(f"Word text extraction error: {str(e)}")
        return "Word document text extraction failed."

@login_required
def get_exemplars(request):
    """Get all exemplars for the current user"""
    try:
        exemplars = Exemplar.objects.filter(user=request.user).order_by('-upload_date')
        serializer = ExemplarSerializer(exemplars, many=True)
        
        return JsonResponse({
            'success': True,
            'exemplars': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error fetching exemplars: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': 'Error fetching exemplars'
        }, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def delete_exemplar(request, exemplar_id):
    """Delete an exemplar"""
    try:
        exemplar = get_object_or_404(Exemplar, id=exemplar_id, user=request.user)
        exemplar_name = exemplar.name
        exemplar.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Exemplar "{exemplar_name}" deleted successfully!'
        })
        
    except Exception as e:
        logger.error(f"Error deleting exemplar: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': 'Error deleting exemplar'
        }, status=500)

@login_required
def get_exemplar_text(request, exemplar_id):
    """Get the extracted text of an exemplar"""
    try:
        exemplar = get_object_or_404(Exemplar, id=exemplar_id, user=request.user)
        
        return JsonResponse({
            'success': True,
            'text': exemplar.extracted_text or 'No text content available.'
        })
        
    except Exception as e:
        logger.error(f"Error fetching exemplar text: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': 'Error fetching exemplar content'
        }, status=500)

@login_required
def supervising_teacher_reviews(request):
    """Supervising teacher's page to review student lesson plans"""
    if request.user.role != 'Teacher':
        messages.error(request, "You are not authorized to access this page.")
        return redirect('dashboard')
    
    # Get pending submissions from supervised students
    pending_submissions = LessonPlanSubmission.objects.filter(
        submitted_to=request.user,
        submitted_by__supervising_teacher=request.user,  # Only students supervised by this teacher
        status='submitted'
    ).select_related('lesson_plan', 'submitted_by').order_by('submission_date')
    
    # Get reviewed submissions for history
    reviewed_submissions = LessonPlanSubmission.objects.filter(
        submitted_to=request.user,
        submitted_by__supervising_teacher=request.user
    ).exclude(status='submitted').select_related('lesson_plan', 'submitted_by').order_by('-review_date')[:10]
    
    context = {
        'user': request.user,
        'pending_submissions': pending_submissions,
        'reviewed_submissions': reviewed_submissions,
        'pending_count': pending_submissions.count(),
    }
    
    return render(request, 'teacher/supervising_teacher_reviews.html', context)

@login_required
def review_student_lesson_plan(request, submission_id):
    """Supervising teacher reviews a student's lesson plan"""
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
                messages.success(request, f"Lesson plan '{submission.lesson_plan.title}' approved successfully!")
            elif action == 'reject':
                submission.status = 'rejected'
                messages.success(request, f"Lesson plan '{submission.lesson_plan.title}' rejected.")
            elif action == 'needs_revision':
                submission.status = 'needs_revision'
                # Change lesson plan back to draft so student can revise
                submission.lesson_plan.status = LessonPlan.DRAFT
                submission.lesson_plan.save()
                messages.success(request, f"Lesson plan '{submission.lesson_plan.title}' returned for revision.")
            
            submission.review_notes = review_notes
            submission.review_date = timezone.now()
            submission.save()
            
            # Create notification for student
            from lessonlinkNotif.models import Notification
            Notification.create_draft_status_notification(submission, approved=(action == 'approve'))
            
        except LessonPlanSubmission.DoesNotExist:
            messages.error(request, "Submission not found.")
        
        return redirect('supervising_teacher_reviews')
    
    return redirect('dashboard')