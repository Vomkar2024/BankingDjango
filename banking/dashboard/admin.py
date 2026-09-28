from django.contrib import admin
from .models import Account, Transaction, DebitCard, Loan, Beneficiary, SupportTicket, Notification


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'user', 'account_type', 'current_balance', 'available_balance', 'is_primary', 'is_active', 'created_at')
    list_filter = ('account_type', 'is_primary', 'is_active', 'created_at')
    search_fields = ('account_number', 'user__username', 'user__first_name', 'user__last_name')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('reference_id', 'account', 'title', 'transaction_type', 'category', 'amount', 'status', 'created_at')
    list_filter = ('transaction_type', 'category', 'status', 'created_at')
    search_fields = ('reference_id', 'title', 'description', 'account__account_number', 'account__user__username')
    readonly_fields = ('created_at',)


@admin.register(DebitCard)
class DebitCardAdmin(admin.ModelAdmin):
    list_display = ('card_holder_name', 'network', 'card_type', 'masked_number', 'expiry_display', 'is_active', 'is_frozen')
    list_filter = ('network', 'card_type', 'is_active', 'is_frozen')
    search_fields = ('card_holder_name', 'card_number', 'account__account_number')


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'user', 'loan_type', 'principal_amount', 'remaining_amount', 'monthly_emi', 'status')
    list_filter = ('loan_type', 'status', 'created_at')
    search_fields = ('account_number', 'user__username')


@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'account_number', 'bank_name', 'nickname', 'created_at')
    search_fields = ('name', 'account_number', 'bank_name', 'user__username')


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'user', 'category', 'subject', 'status', 'created_at')
    list_filter = ('category', 'status', 'created_at')
    search_fields = ('ticket_id', 'subject', 'message', 'user__username')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')
