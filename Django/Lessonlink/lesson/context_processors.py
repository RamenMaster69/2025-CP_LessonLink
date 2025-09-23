def user_school_info(request):
    """Add school and department information to all templates"""
    if request.user.is_authenticated:
        return {
            'user_school': request.user.school,
            'user_department': request.user.department,
            'user_role': request.user.role,
        }
    return {}