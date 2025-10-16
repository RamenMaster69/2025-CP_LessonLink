from django.utils import timezone
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from datetime import datetime

class AutoLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(f"🔵 MIDDLEWARE - Path: {request.path}, User: {request.user}, Authenticated: {request.user.is_authenticated}")
        
        # Skip if user is not authenticated
        if not request.user.is_authenticated:
            print("🔵 User not authenticated, skipping timeout check")
            return self.get_response(request)

        # Get current time and last activity
        now = timezone.now()
        last_activity = request.session.get('last_activity')
        
        if last_activity:
            last_activity_time = datetime.fromisoformat(last_activity)
            elapsed = (now - last_activity_time).total_seconds()
            
            print(f"🔵 User IS authenticated! Last activity was {elapsed:.1f} seconds ago")

            # Check if inactive for more than 2 seconds
            if elapsed > 300:
                print("⚠️⚠️⚠️ TIMEOUT! User inactive for >2 seconds ⚠️⚠️⚠️")
                print(f"⚠️⚠️⚠️ Logging out user: {request.user.email} ⚠️⚠️⚠️")
                
                # ✅ Create redirect FIRST, then logout
                logout(request)
                
                # ✅ Use HttpResponseRedirect and manually construct URL
                redirect_url = '/login/?timeout=1'
                print(f"⚠️⚠️⚠️ Redirecting to {redirect_url} ⚠️⚠️⚠️")
                
                response = HttpResponseRedirect(redirect_url)
                return response
            else:
                print(f"✅ User still active (elapsed: {elapsed:.1f}s < 2s)")
        else:
            print("🔵 First request for this user, setting last_activity")

        # Update last activity time
        request.session['last_activity'] = now.isoformat()
        print(f"🔵 Updated last_activity to: {now.isoformat()}")
        
        return self.get_response(request)