from django.shortcuts import render

# Create your views here.
def landing(request):
    return render(request, 'landing.html')

def registration_1(request):
    return render(request, 'registration_1.html')

def registration_2(request):
    return render(request, 'registration_2.html')