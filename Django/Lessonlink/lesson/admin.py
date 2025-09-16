from django.contrib import admin
from .models import User, Schedule, Task, SchoolRegistration  # Import SchoolRegistration


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

    @admin.display(boolean=True, description="Overdue?")
    def is_overdue(self, obj):
        return obj.is_overdue()


@admin.register(SchoolRegistration)
class SchoolRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'school_name', 'school_id', 'year_established', 'address', 'province', 'region',
        'phone_number', 'email', 'website', 'facebook_page',
        'contact_person', 'position', 'contact_email', 'contact_phone',
        'accuracy', 'terms', 'communications', 'status', 'created_at'
    )
    search_fields = (
        'school_name', 'school_id', 'email', 'contact_person', 'address', 'province', 'region'
    )
    list_filter = ('status', 'province', 'region', 'accuracy', 'terms', 'communications')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('School Information', {
            'fields': ('school_name', 'school_id', 'year_established', 'address', 'province', 'region')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'email', 'website', 'facebook_page', 'contact_person', 'position', 'contact_email', 'contact_phone')
        }),
        ('Agreements', {
            'fields': ('accuracy', 'terms', 'communications')
        }),
        ('Status & Timestamps', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )
