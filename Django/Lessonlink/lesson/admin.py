from django.contrib import admin
from .models import User  # Import your custom User model
from .models import Schedule
from .models import Task


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'department')
    search_fields = ('email', 'first_name', 'last_name', 'role')
    list_filter = ('role', 'department')

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'day', 'time')
    list_filter = ('day', 'time', 'user')
    search_fields = ('subject', 'description')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'user', 
        'priority', 
        'status', 
        'display_due_datetime', 
        'is_overdue'
    )
    list_filter = ('priority', 'status', 'due_date')
    search_fields = ('title', 'description', 'user__email', 'user__first_name', 'user__last_name')
    ordering = ('-created_at',)

    # make "is_overdue" display as a boolean icon
    @admin.display(boolean=True, description="Overdue?")
    def is_overdue(self, obj):
        return obj.is_overdue()