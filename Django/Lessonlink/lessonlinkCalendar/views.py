# lessonlinkCalendar/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json
from .models import CalendarActivity

@login_required
@csrf_exempt
@require_http_methods(["GET"])
def get_calendar_activities(request):
    """Get activities for the current user"""
    activities = CalendarActivity.objects.filter(user=request.user)
    
    activities_data = []
    for activity in activities:
        activities_data.append({
            'id': activity.id,
            'title': activity.title,
            'description': activity.description,
            'startDate': activity.start_date.isoformat(),
            'endDate': activity.end_date.isoformat() if activity.end_date else None,
            'category': activity.category,
        })
    
    return JsonResponse(activities_data, safe=False)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def add_calendar_activity(request):
    """Add a new activity for the current user"""
    try:
        data = json.loads(request.body)
        activity = CalendarActivity(
            user=request.user,
            title=data['title'],
            description=data.get('description', ''),
            start_date=data['startDate'],
            end_date=data.get('endDate', data['startDate']),
            category=data['category']
        )
        activity.save()
        
        return JsonResponse({
            'id': activity.id,
            'success': True
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@csrf_exempt
@require_http_methods(["DELETE"])
def delete_calendar_activity(request, activity_id):
    """Delete an activity (only if owned by user)"""
    try:
        activity = CalendarActivity.objects.get(id=activity_id, user=request.user)
        activity.delete()
        return JsonResponse({'success': True})
    except CalendarActivity.DoesNotExist:
        return JsonResponse({'error': 'Activity not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)