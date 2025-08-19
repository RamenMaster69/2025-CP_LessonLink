from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .models import User
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage 

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
    return render(request, 'registration_1.html')

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

    return render(request, 'registration_2.html')

def registration_3(request):
    # Check if user came from previous steps
    if not request.session.get('reg_email') or not request.session.get('reg_first_name'):
        messages.error(request, "Please complete the previous registration steps.")
        return redirect('registration_1')
    
    if request.method == 'POST':
        role = request.POST.get('role')
        rank = request.POST.get('rank')

        if not role or not rank:
            messages.error(request, "Please select both role and rank.")
            return render(request, 'registration_3.html', {
                'role': role,
                'rank': rank,
                'error_message': "Please select both role and rank.",
                'show_error': True
            })

        # Store in session
        request.session['reg_role'] = role
        request.session['reg_rank'] = rank

        messages.success(request, "Role and rank selected successfully!")
        return redirect('registration_4')

    return render(request, 'registration_3.html')

def registration_4(request):
    # Check if user came from previous steps
    if not request.session.get('reg_email') or not request.session.get('reg_role'):
        messages.error(request, "Please complete the previous registration steps.")
        return redirect('registration_1')
    
    if request.method == "POST":
        department = request.POST.get("department")
        specialization = request.POST.get("specialization")
        affiliations = request.POST.getlist("affiliation[]")

        if not department or not specialization:
            messages.error(request, "Please complete all required fields.")
            return render(request, 'registration_4.html', {
                'department': department,
                'specialization': specialization,
                'affiliations': affiliations,
                'error_message': "Please complete all required fields.",
                'show_error': True
            })

        # Get all session data
        email = request.session.get('reg_email')
        raw_password = request.session.get('reg_password')
        first_name = request.session.get('reg_first_name')
        middle_name = request.session.get('reg_middle_name', '')
        last_name = request.session.get('reg_last_name')
        dob = request.session.get('reg_dob')
        role = request.session.get('reg_role')
        rank = request.session.get('reg_rank')

        # Double-check session data integrity
        if not email or not raw_password:
            messages.error(request, "Session expired. Please restart registration.")
            # Clear any partial session data
            for key in list(request.session.keys()):
                if key.startswith("reg_"):
                    del request.session[key]
            return redirect('registration_1')

        try:
            # Final check for email existence (in case of race condition)
            if User.objects.filter(email=email).exists():
                messages.error(request, "This email was registered by someone else. Please use a different email.")
                # Clear session and restart
                for key in list(request.session.keys()):
                    if key.startswith("reg_"):
                        del request.session[key]
                return redirect('registration_1')

            # Create the user
            user = User.objects.create(
                email=email,
                password=make_password(raw_password),
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                dob=dob,
                role=role,
                rank=rank,
                department=department,
                specialization=specialization,
                affiliations=", ".join(affiliations) if affiliations else ""
            )

            # Clear all registration session data
            for key in list(request.session.keys()):
                if key.startswith("reg_"):
                    del request.session[key]

            # Success message and redirect to login
            messages.success(request, f"Account created successfully for {email}! Please log in with your credentials.")
            return redirect('login')

        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return render(request, 'registration_4.html', {
                'department': department,
                'specialization': specialization,
                'affiliations': affiliations,
                'error_message': f"Registration failed: {str(e)}",
                'show_error': True
            })

    return render(request, 'registration_4.html')

def login_view(request):
    # If user is already logged in, redirect to dashboard
    if request.session.get('user_id'):
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

        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                request.session['user_id'] = user.id
                messages.success(request, f"Welcome back, {user.first_name}!")
                return redirect('dashboard')
            else:
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

def dashboard(request):
    # Check if user is logged in
    user_id = request.session.get('user_id')
    
    if not user_id:
        messages.error(request, "Please log in to access the dashboard.")
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
        return render(request, 'dashboard.html', {
            'user': user,
            'full_name': f"{user.first_name} {user.middle_name} {user.last_name}".strip()
        })
    except User.DoesNotExist:
        messages.error(request, "User account not found. Please log in again.")
        # Clear the invalid session
        if 'user_id' in request.session:
            del request.session['user_id']
        return redirect('login')

def logout_view(request):
    """Logout user and clear session"""
    if 'user_id' in request.session:
        del request.session['user_id']
    
    # Clear any remaining registration data
    for key in list(request.session.keys()):
        if key.startswith("reg_"):
            del request.session[key]
    
    messages.success(request, "You have been logged out successfully.")
    return redirect('landing')

from django.core.files.storage import default_storage  # Make sure this import exists

def profile(request):
    # Check if user is logged in
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Please log in to view your profile.")
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
        
        if request.method == 'POST':
            # Handle profile picture upload
            if 'profile_picture' in request.FILES:
                # Delete old profile picture if exists
                if user.profile_picture:
                    default_storage.delete(user.profile_picture.path)
                user.profile_picture = request.FILES['profile_picture']
            
            # Update all fields - ensure you're getting ALL fields from the form
            user.first_name = request.POST.get('first_name', user.first_name)
            user.middle_name = request.POST.get('middle_name', user.middle_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.dob = request.POST.get('dob', user.dob)
            user.role = request.POST.get('role', user.role)
            user.rank = request.POST.get('rank', user.rank)
            user.department = request.POST.get('department', user.department)
            user.specialization = request.POST.get('specialization', user.specialization)
            user.affiliations = request.POST.get('affiliations', user.affiliations)
            
            try:
                user.save()
                messages.success(request, "Profile updated successfully!")
                return redirect('profile')  # CRITICAL: Add this redirect
            except Exception as e:
                messages.error(request, f"Error updating profile: {str(e)}")
                # Stay on same page to show errors
        
        # GET request - show profile
        return render(request, 'profile.html', {
            'user': user,
            'full_name': f"{user.first_name} {user.middle_name} {user.last_name}".strip()
        })
    
    except User.DoesNotExist:
        messages.error(request, "User account not found. Please log in again.")
        if 'user_id' in request.session:
            del request.session['user_id']
        return redirect('login')
def lesson_planner(request):
    # Check if user is logged in
    user_id = request.session.get('user_id')
    
    if not user_id:
        messages.error(request, "Please log in to access the lesson planner.")
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
        return render(request, 'lesson_planner.html', {'user': user})
    except User.DoesNotExist:
        messages.error(request, "User account not found. Please log in again.")
        # Clear the invalid session
        if 'user_id' in request.session:
            del request.session['user_id']
        return redirect('login')

def draft(request):
    # Check if user is logged in
    user_id = request.session.get('user_id')
    
    if not user_id:
        messages.error(request, "Please log in to access drafts.")
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
        return render(request, 'draft.html', {'user': user})
    except User.DoesNotExist:
        messages.error(request, "User account not found. Please log in again.")
        # Clear the invalid session
        if 'user_id' in request.session:
            del request.session['user_id']
        return redirect('login')
    return render(request, 'draft.html')

def task(request):
    user_id = request.session.get('user_id')
    user = None
    if user_id:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            user = None
    return render(request, 'task.html', {'user': user})

def Dep_Dash(request):
    return render(request, 'Dep_Dash.html')

def Dep_Faculty(request):
    return render(request, 'Dep_Faculty.html')

def schedule(request):
    return render(request, 'schedule.html')

def faculty_draft(request):
    return render(request, 'faculty_draft.html')

def Dep_Pending(request):
    return render(request, 'Dep_Pending.html')

def template(request):
    return render(request, 'template.html')
