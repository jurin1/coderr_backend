from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from rest_framework.authtoken.models import Token
from .models import CustomUser 

# @admin.register(Token)
# class TokenAdmin(admin.ModelAdmin):
#     list_display = ('key', 'user', 'created')





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