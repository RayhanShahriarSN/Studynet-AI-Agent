from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from django.utils.translation import gettext_lazy as _



class UserAdmin(BaseUserAdmin):
    # Fields to display in admin list view
    list_display = ('id', 'username', 'email', 'is_admin', 'is_active','tokens_used')  # replaced 'name' with 'username'
    list_filter = ('is_admin', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('id',)

    # Fields for the add user/edit user
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password', 'tokens_used')}),
        (_('Permissions'), {'fields': ('is_admin', 'is_active')}),
        (_('Important dates'), {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_admin', 'is_active', 'tokens_used')}
        ),
    )

    filter_horizontal = ()

# Register the updated UserAdmin
admin.site.register(User, UserAdmin)
