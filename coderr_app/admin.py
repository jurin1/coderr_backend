from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile, Offer, OfferDetail, Review
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

class OfferDetailInline(admin.TabularInline):  
    model = OfferDetail
    extra = 1  
@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    inlines = [OfferDetailInline]
    list_display = ('title', 'user', 'min_price', 'min_delivery_time', 'created_at', 'updated_at') 
    list_filter = ('created_at', 'updated_at')      
    search_fields = ('title', 'description', 'user__username') 
    readonly_fields = ('min_price', 'min_delivery_time', 'created_at', 'updated_at') 
    raw_id_fields = ('user',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'business_user', 'rating', 'created_at')
    search_fields = ('reviewer__username', 'business_user__username', 'description')
    list_filter = ('rating', 'created_at')
    raw_id_fields = ('reviewer', 'business_user')