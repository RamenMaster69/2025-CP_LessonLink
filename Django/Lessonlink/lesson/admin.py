from django.contrib import admin
from .models import User  # Import your custom User model
from .models import ClassSchedule


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'department')
    search_fields = ('email', 'first_name', 'last_name', 'role')
    list_filter = ('role', 'department')


class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = ('subject', 'day', 'time', 'created_at')
    list_filter = ('day', 'time')
    search_fields = ('subject', 'description')

admin.site.register(ClassSchedule, ClassScheduleAdmin)
