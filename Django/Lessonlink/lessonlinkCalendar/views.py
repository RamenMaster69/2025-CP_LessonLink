from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import CalendarActivity

def calendar_view(request):
    return render(request, 'dep_calendar.html')  # Looks in templates folder

@csrf_exempt
def activities_api(request):
    if request.method == 'GET':
        activities = CalendarActivity.objects.all()
        activities_data = []
        
        for activity in activities:
            activities_data.append({
                'id': activity.id,
                'title': activity.title,
                'description': activity.description,
                'startDate': activity.start_date.isoformat(),
                'endDate': activity.end_date.isoformat(),
                'category': activity.category
            })
        
        return JsonResponse(activities_data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            activity = CalendarActivity(
                title=data['title'],
                description=data.get('description', ''),
                start_date=data['startDate'],
                end_date=data.get('endDate', data['startDate']),
                category=data['category']
            )
            activity.save()
            
            return JsonResponse({
                'id': activity.id,
                'title': activity.title,
                'description': activity.description,
                'startDate': activity.start_date.isoformat(),
                'endDate': activity.end_date.isoformat(),
                'category': activity.category
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def delete_activity(request, activity_id):
    if request.method == 'DELETE':
        try:
            activity = CalendarActivity.objects.get(id=activity_id)
            activity.delete()
            return JsonResponse({'success': True})
        except CalendarActivity.DoesNotExist:
            return JsonResponse({'error': 'Activity not found'}, status=404)