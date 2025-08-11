from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .models import User  # ✅ Your custom User model

def landing(request):
    return render(request, 'landing.html')

def registration_1(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')

        if not email or not password or not confirm_password:
            messages.error(request, "Please fill in all fields.")
            return redirect('registration_1')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('registration_1')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return redirect('registration_1')

        request.session['reg_email'] = email
        request.session['reg_password'] = password
        return redirect('registration_2')

    return render(request, 'registration_1.html')

def registration_2(request):
    if request.method == 'POST':
        first_name = request.POST.get('firstName')
        middle_name = request.POST.get('middleName')
        last_name = request.POST.get('lastName')
        dob = request.POST.get('dateOfBirth')

        if not first_name or not last_name or not dob:
            messages.error(request, "Please fill in all required fields.")
            return redirect('registration_2')

        request.session['reg_first_name'] = first_name
        request.session['reg_middle_name'] = middle_name
        request.session['reg_last_name'] = last_name
        request.session['reg_dob'] = dob

        return redirect('registration_3')

    return render(request, 'registration_2.html')

def registration_3(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        rank = request.POST.get('rank')

        if not role or not rank:
            messages.error(request, "Please select both role and rank.")
            return redirect('registration_3')

        request.session['reg_role'] = role
        request.session['reg_rank'] = rank

        return redirect('registration_4')

    return render(request, 'registration_3.html')

def registration_4(request):
    if request.method == "POST":
        department = request.POST.get("department")
        specialization = request.POST.get("specialization")
        affiliations = request.POST.getlist("affiliation[]")

        if not department or not specialization:
            messages.error(request, "Please complete all required fields.")
            return redirect('registration_4')

        # Get session data
        email = request.session.get('reg_email')
        raw_password = request.session.get('reg_password')
        first_name = request.session.get('reg_first_name')
        middle_name = request.session.get('reg_middle_name')
        last_name = request.session.get('reg_last_name')
        dob = request.session.get('reg_dob')
        role = request.session.get('reg_role')
        rank = request.session.get('reg_rank')

        if not email or not raw_password:
            messages.error(request, "Session expired. Please restart registration.")
            return redirect('registration_1')

        # Save to your custom User model
        User.objects.create(
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
            affiliations=", ".join(affiliations)
        )

        # Clear session data
        for key in list(request.session.keys()):
            if key.startswith("reg_"):
                del request.session[key]

        messages.success(request, "Registration complete!")
        return redirect('dashboard')

    return render(request, 'registration_4.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                request.session['user_id'] = user.id
                messages.success(request, "Login successful!")
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid password.")
        except User.DoesNotExist:
            messages.error(request, "Email not registered.")

    return render(request, 'login.html')

def dashboard(request):
    user_id = request.session.get('user_id')
    user = None

    if user_id:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, "User not found. Please log in again.")
            return redirect('login')

    return render(request, 'dashboard.html', {'user': user})

def profile(request):
    return render(request, 'profile.html')

def lesson_planner(request):
    return render(request, 'lesson_planner.html')

def draft(request):
    return render(request, 'draft.html')
