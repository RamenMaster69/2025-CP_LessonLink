from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Schedule, Task, SchoolRegistration
from lessonlinkCalendar.models import ZamboangaEvent  # ADD THIS IMPORT


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("email", "first_name", "last_name", "role", "department", "school", "supervising_teacher", "is_staff")
    list_filter = ("role", "department", "school", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name", "supervising_teacher__email")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "middle_name", "last_name", "dob", "profile_picture")}),
        ("School info", {"fields": ("role", "rank", "department", "school", "supervising_teacher", "affiliations")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "first_name",
                "last_name",
                "role",
                "rank",
                "department",
                "school",
                "supervising_teacher",  # Add this field
                "password1",
                "password2",
                "is_staff",
                "is_active",
            )}
        ),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Limit supervising_teacher choices to Teachers only"""
        if db_field.name == "supervising_teacher":
            kwargs["queryset"] = User.objects.filter(role='Teacher', is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


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


@admin.register(ZamboangaEvent)
class ZamboangaEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_month', 'start_day', 'duration_days', 'category', 'is_active']
    list_filter = ['category', 'is_active', 'is_annual']
    search_fields = ['title', 'description']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Event Details', {
            'fields': ('title', 'description', 'category', 'organizer', 'location')
        }),
        ('Date Information', {
            'fields': ('start_month', 'start_day', 'duration_days'),
            'description': 'Event will automatically occur on these dates every year'
        }),
        ('Settings', {
            'fields': ('is_annual', 'is_active', 'notes')
        }),
    )