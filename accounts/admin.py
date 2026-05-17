from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


# Unregister first in case it was auto-registered elsewhere
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    # What shows in the list — this is what replaces "CustomUser object"
    list_display  = ['full_name', 'email', 'role', 'is_active', 'is_staff']
    list_filter   = ['role', 'is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']
    ordering      = ['first_name']

    # Fields shown when editing a user in admin
    fieldsets = (
        ('Personal Info',   {'fields': ('first_name', 'last_name', 'email', 'password')}),
        ('Role & Access',   {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Extra',           {'fields': ('organization', 'phone')}),
        ('Permissions',     {'fields': ('groups', 'user_permissions')}),
        ('Dates',           {'fields': ('date_joined', 'last_login')}),
    )

    # Fields shown when CREATING a new user from admin panel
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email', 'password1', 'password2'),
        }),
    )

    readonly_fields = ['date_joined', 'last_login']

    # This controls the display name in the list
    def full_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name if name else obj.email
    full_name.short_description = 'Name'