from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (
    User, Schedule, Task, TaskNotification, 
    SchoolRegistration, AdminLog, StudentConcern, 
    SystemSettings, SchoolAdmin, LessonPlanSubmission, 
    Exemplar, EmailTemplate, Province
)
from lessonlinkCalendar.models import ZamboangaEvent


# Custom User Admin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("email", "first_name", "last_name", "role", "department", "school", "is_staff", "is_active")
    list_filter = ("role", "department", "school", "is_staff", "is_active", "approval_status")
    search_fields = ("email", "first_name", "last_name", "supervising_teacher__email")
    ordering = ("email",)
    
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "middle_name", "last_name", "dob", "profile_picture")}),
        ("School info", {"fields": ("role", "rank", "department", "school", "supervising_teacher", "affiliations")}),
        ("Approval Status", {"fields": ("approval_status", "rejection_reason")}),
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
                "supervising_teacher",
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


# School Registration Admin
@admin.register(SchoolRegistration)
class SchoolRegistrationAdmin(admin.ModelAdmin):
    list_display = ('school_name', 'school_id', 'region', 'status', 'contact_person', 'contact_email', 'created_at')
    list_filter = ('status', 'region', 'created_at', 'accuracy', 'terms')
    search_fields = ('school_name', 'school_id', 'contact_person', 'contact_email', 'email', 'phone_number')
    readonly_fields = ('created_at', 'updated_at', 'processed_at', 'logo_preview')
    list_editable = ('status',)
    
    fieldsets = (
        ('Institution Details', {
            'fields': ('school_name', 'school_id', 'year_established', 'school_logo', 'logo_preview')
        }),
        ('Contact Information', {
            'fields': ('address', 'region', 'province', 'phone_number', 'email', 'website', 'facebook_page')
        }),
        ('Administrative Contact', {
            'fields': ('contact_person', 'position', 'contact_email', 'contact_phone')
        }),
        ('Agreements', {
            'fields': ('accuracy', 'terms', 'communications')
        }),
        ('Administration', {
            'fields': ('status', 'admin_notes', 'password_hash')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processed_at', 'processed_by'),
            'classes': ('collapse',)
        }),
    )
    
    def logo_preview(self, obj):
        if obj.school_logo:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.school_logo.url)
        return "No logo uploaded"
    logo_preview.short_description = 'Logo Preview'
    
    actions = ['approve_selected', 'reject_selected', 'mark_pending']
    
    def approve_selected(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} school(s) approved successfully.')
    approve_selected.short_description = "Approve selected schools"
    
    def reject_selected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} school(s) rejected.')
    reject_selected.short_description = "Reject selected schools"
    
    def mark_pending(self, request, queryset):
        updated = queryset.update(status='pending')
        self.message_user(request, f'{updated} school(s) marked as pending.')
    mark_pending.short_description = "Mark as pending"


# Schedule Admin
@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'day', 'time')
    list_filter = ('day', 'time', 'user')
    search_fields = ('subject', 'description', 'user__email')


# Task Admin
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'priority', 'status', 'display_due_datetime', 'is_overdue')
    list_filter = ('priority', 'status', 'due_date')
    search_fields = ('title', 'description', 'user__email')
    ordering = ('-created_at',)
    
    @admin.display(boolean=True, description="Overdue?")
    def is_overdue(self, obj):
        return obj.is_overdue()


# Task Notification Admin
@admin.register(TaskNotification)
class TaskNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('message', 'user__email', 'task__title')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


# Admin Log Admin
@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ('admin', 'action', 'target_user', 'target_school', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('admin__email', 'target_user__email', 'description', 'ip_address')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)


# Student Concern Admin
@admin.register(StudentConcern)
class StudentConcernAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'concern_type', 'status', 'created_at')
    list_filter = ('concern_type', 'status', 'created_at')
    search_fields = ('subject', 'content', 'student__email')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


# System Settings Admin
@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'description', 'updated_at')
    search_fields = ('key', 'description')
    readonly_fields = ('updated_at', 'updated_by')


# School Admin Admin
@admin.register(SchoolAdmin)
class SchoolAdminAdmin(admin.ModelAdmin):
    list_display = ('user', 'school', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'school')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'school__school_name')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


# Lesson Plan Submission Admin
@admin.register(LessonPlanSubmission)
class LessonPlanSubmissionAdmin(admin.ModelAdmin):
    list_display = ('lesson_plan', 'submitted_by', 'submitted_to', 'status', 'submission_date')
    list_filter = ('status', 'submission_date')
    search_fields = ('lesson_plan__title', 'submitted_by__email', 'submitted_to__email')
    readonly_fields = ('submission_date', 'review_date')
    ordering = ('-submission_date',)


# Exemplar Admin
@admin.register(Exemplar)
class ExemplarAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'file_type', 'file_size', 'upload_date', 'department')
    list_filter = ('file_type', 'upload_date', 'department')
    search_fields = ('name', 'user__email', 'extracted_text')
    readonly_fields = ('upload_date', 'file_size')
    ordering = ('-upload_date',)
    
    def file_size(self, obj):
        return obj.get_file_size_display()
    file_size.short_description = 'File Size'


# Email Template Admin
@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('template_type', 'subject', 'is_active', 'updated_at')
    list_filter = ('is_active', 'template_type')
    search_fields = ('subject', 'body')
    readonly_fields = ('created_at', 'updated_at')


# Province Admin
@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'region_code')
    list_filter = ('region',)
    search_fields = ('name', 'region')
    ordering = ('name',)


# Zamboanga Event Admin
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


# Optional: Customize admin site header
admin.site.site_header = "LessonLink Administration"
admin.site.site_title = "LessonLink Admin Portal"
admin.site.index_title = "Welcome to LessonLink Administration"