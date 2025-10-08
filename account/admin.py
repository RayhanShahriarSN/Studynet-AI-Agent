# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

class UserAdmin(BaseUserAdmin):
    # Fields to display in admin list view
    list_display = ('id', 'username', 'email', 'is_admin', 'is_active', 'tokens_used', 'bearer_token_display')  
    list_filter = ('is_admin', 'is_active')
    search_fields = ('username', 'email', 'bearer_token') 
    ordering = ('id',)
    
    # Custom actions
    actions = ['regenerate_bearer_tokens']

    # Fields for the add user/edit user
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),  
        (_('Token Information'), {'fields': ('tokens_used', 'bearer_token')}),
        (_('Permissions'), {'fields': ('is_admin', 'is_active')}),
        (_('Important dates'), {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_login')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_admin', 'is_active'),
        }),
    )

    filter_horizontal = ()
    
    def bearer_token_display(self, obj):
        """Display bearer token with copy functionality"""
        if obj.bearer_token:
            return format_html(
                '<code style="background: #f0f0f0; padding: 5px; border-radius: 3px;">{}</code>',
                obj.bearer_token[:20] + '...' if len(obj.bearer_token) > 20 else obj.bearer_token
            )
        return '-'
    bearer_token_display.short_description = 'Bearer Token'
    
    def regenerate_bearer_tokens(self, request, queryset):
        """Admin action to regenerate bearer tokens for selected users"""
        count = 0
        for user in queryset:
            user.regenerate_bearer_token()
            count += 1
        self.message_user(request, f'Successfully regenerated bearer tokens for {count} user(s).')
    regenerate_bearer_tokens.short_description = 'Regenerate bearer tokens for selected users'

# Register the updated UserAdmin
admin.site.register(User, UserAdmin)