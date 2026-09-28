from django.contrib import admin
from .models import CustomerProfile


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'city', 'kyc_status', 'account_tier', 'created_at')
    list_filter = ('kyc_status', 'account_tier', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone_number', 'pan_number')
