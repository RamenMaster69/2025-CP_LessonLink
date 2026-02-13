# context_processors.py
def user_school_info(request):
    if request.user.is_authenticated:
        try:
            return {
                'user_school': request.user.school,
            }
        except Exception as e:
            print(f"Context processor error: {e}")
            return {}
    return {}