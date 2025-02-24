from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from rest_framework.authtoken.models import Token
from .models import CustomUser, Profile, FileUpload 
from django.utils.html import format_html

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'email', 'created_at')  
    search_fields = ('user__username', 'first_name', 'last_name', 'email')  
    list_filter = ('created_at',) 
    raw_id_fields = ('user',)

    def email(self, obj):
        return obj.user.email
    email.short_description = 'User Email' 

  
    readonly_fields = ('created_at',)

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'type', 'is_staff']  
    fieldsets = UserAdmin.fieldsets + (  
        (None, {'fields': ('type',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('type',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)