# lessonlinkCalendar/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
import json
from .models import CalendarActivity

@login_required
@csrf_exempt
@require_http_methods(["GET"])
def get_calendar_activities(request):
    """Get activities for the same school with proper permissions"""
    user = request.user
    
    print(f"=== GET CALENDAR ACTIVITIES ===")
    print(f"User: {user.email}, Role: {user.role}, School: {user.school}")
    
    # Get activities based on user's school
    if user.school:
        # Show activities from the same school only (NO DEPARTMENT FILTERING)
        activities = CalendarActivity.objects.filter(school=user.school)
        print(f"Activities found for school '{user.school}': {activities.count()}")
    else:
        # For users without school (admin), show all activities
        activities = CalendarActivity.objects.all()
        print(f"Admin view - showing all activities: {activities.count()}")
    
    # Debug: List all activities found with details
    print("=== ACTIVITIES FOUND ===")
    for activity in activities:
        print(f"  - '{activity.title}' by {activity.user.email} (School: {activity.school})")
    
    activities_data = []
    for activity in activities:
        can_edit = activity.can_edit(user)
        can_delete = activity.can_delete(user)
        
        print(f"PERMISSIONS - Activity '{activity.title}':")
        print(f"  can_edit={can_edit}, can_delete={can_delete}")
        
        # Handle date formatting safely
        try:
            start_date = activity.start_date.isoformat() if hasattr(activity.start_date, 'isoformat') else str(activity.start_date)
            end_date = activity.end_date.isoformat() if activity.end_date and hasattr(activity.end_date, 'isoformat') else str(activity.end_date or activity.start_date)
        except AttributeError:
            start_date = str(activity.start_date)
            end_date = str(activity.end_date) if activity.end_date else start_date
        
        activities_data.append({
            'id': activity.id,
            'title': activity.title,
            'description': activity.description,
            'startDate': start_date,
            'endDate': end_date,
            'category': activity.category,
            'author': f"{activity.user.first_name} {activity.user.last_name}",  # FIXED: self.user to activity.user
            'user': {
                'id': activity.user.id,
                'is_superuser': activity.user.is_superuser,
                'username': activity.user.email
            },
            'canEdit': can_edit,
            'canDelete': can_delete
        })
    
    print(f"Returning {len(activities_data)} activities to frontend")
    print("===============================")
    
    return JsonResponse(activities_data, safe=False)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def add_calendar_activity(request):
    """Add a new activity for the current user with permission checking"""
    try:
        user = request.user
        
        # DEBUG: Print user info
        print(f"=== ADD CALENDAR ACTIVITY ===")
        print(f"User: {user.email}")
        print(f"User Role: {user.role}")
        
        # ENFORCE PERMISSIONS: Teachers cannot add activities
        if user.role == 'teacher' or user.role == 'Student Teacher':
            print("PERMISSION DENIED: Teacher cannot add activities")
            return JsonResponse({
                'success': False, 
                'error': 'You are not authorized to add activities.'
            }, status=403)
        
        data = json.loads(request.body)
        print(f"Received data: {data}")
        
        # Validate required fields
        required_fields = ['title', 'startDate', 'category']
        missing_fields = []
        for field in required_fields:
            if not data.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"Missing required fields: {missing_fields}")
            return JsonResponse({
                'success': False, 
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=400)
        
        # Create the activity
        activity = CalendarActivity(
            user=user,
            title=data['title'],
            description=data.get('description', ''),
            start_date=data['startDate'],
            end_date=data.get('endDate', data['startDate']),
            category=data['category'],
            school=user.school,  # Add school information
            department=user.department  # Add department information
        )
        activity.save()
        
        print(f"Activity created successfully: '{activity.title}'")
        print(f"Activity saved with School: {activity.school}, Department: {activity.department}")
        print(f"Start date: {activity.start_date} (type: {type(activity.start_date)})")
        print(f"End date: {activity.end_date} (type: {type(activity.end_date)})")
        print("===============================")
        
        # FIX: Handle both string and date objects safely
        try:
            # Try to use isoformat if it's a date object
            start_date = activity.start_date.isoformat() if hasattr(activity.start_date, 'isoformat') else str(activity.start_date)
            end_date = activity.end_date.isoformat() if activity.end_date and hasattr(activity.end_date, 'isoformat') else str(activity.end_date or activity.start_date)
        except AttributeError:
            # Fallback to string conversion
            start_date = str(activity.start_date)
            end_date = str(activity.end_date) if activity.end_date else start_date
        
        # Return the activity with all necessary data
        return JsonResponse({
            'success': True,
            'activity': {
                'id': activity.id,
                'title': activity.title,
                'description': activity.description,
                'startDate': start_date,
                'endDate': end_date,
                'category': activity.category,
                'author': f"{activity.user.first_name} {activity.user.last_name}",
                'user': {
                    'id': activity.user.id,
                    'is_superuser': activity.user.is_superuser,
                    'username': activity.user.email
                },
                'canEdit': True,  # User can edit their own activity
                'canDelete': True  # User can delete their own activity
            }
        })
        
    except Exception as e:
        print(f"ERROR in add_calendar_activity: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@csrf_exempt
@require_http_methods(["DELETE"])
def delete_calendar_activity(request, activity_id):
    """Delete an activity with permission checking"""
    try:
        user = request.user
        
        print(f"=== DELETE CALENDAR ACTIVITY ===")
        print(f"User: {user.email}")
        print(f"Attempting to delete activity ID: {activity_id}")
        
        activity = CalendarActivity.objects.get(id=activity_id)
        
        # Check if user can delete this activity
        if not activity.can_delete(user):
            print(f"PERMISSION DENIED: User cannot delete activity '{activity.title}'")
            return JsonResponse({
                'success': False, 
                'error': 'You are not authorized to delete this activity.'
            }, status=403)
        
        print(f"Deleting activity: '{activity.title}'")
        activity.delete()
        print("Activity deleted successfully")
        print("===============================")
        
        return JsonResponse({'success': True})
        
    except CalendarActivity.DoesNotExist:
        print(f"Activity with ID {activity_id} not found")
        return JsonResponse({
            'success': False,
            'error': 'Activity not found'
        }, status=404)
    except Exception as e:
        print(f"ERROR in delete_calendar_activity: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)