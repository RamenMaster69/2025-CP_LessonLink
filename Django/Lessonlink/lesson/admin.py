from django.contrib import admin
from .models import User  # Import your custom User model

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'department')
    search_fields = ('email', 'first_name', 'last_name', 'role')
    list_filter = ('role', 'department')
