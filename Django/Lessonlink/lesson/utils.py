from django.contrib.auth import get_user_model
User = get_user_model()

def get_department_head(teacher):
    """
    Find the appropriate department head for a teacher
    Ensures same school and department matching
    """
    if not teacher.school or not teacher.department:
        return None, "Teacher is not assigned to a school or department."
    
    # Look for active department head in same school and department
    department_head = User.objects.filter(
        role='Department Head',
        department=teacher.department,
        school=teacher.school,
        is_active=True
    ).first()
    
    if department_head:
        return department_head, None
    else:
        return None, f"No Department Head found for {teacher.department} in {teacher.school}"

def validate_school_department_match(user1, user2):
    """Validate that two users are in the same school and department"""
    errors = []
    
    if not user1.school or not user2.school:
        errors.append("Both users must be assigned to a school.")
    
    if not user1.department or not user2.department:
        errors.append("Both users must be assigned to a department.")
    
    if user1.school != user2.school:
        errors.append(f"Users are in different schools: {user1.school} vs {user2.school}")
    
    if user1.department != user2.department:
        errors.append(f"Users are in different departments: {user1.department} vs {user2.department}")
    
    return errors