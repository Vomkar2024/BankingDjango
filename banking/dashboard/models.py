import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def format_inr(amount):
    """Formats a decimal amount in Indian Rupee format e.g. 1,25,450.00"""
    try:
        val = Decimal(amount)
    except Exception:
        return f"{amount}"
    
    is_neg = val < 0
    val = abs(val)
    parts = f"{val:.2f}".split(".")
    int_part = parts[0]
    dec_part = parts[1]

    if len(int_part) <= 3:
        formatted_int = int_part
    else:
        last3 = int_part[-3:]
        rest = int_part[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        formatted_int = ",".join(groups) + "," + last3

    sign = "-" if is_neg else ""
    return f"{sign}₹{formatted_int}.{dec_part}"


class Account(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('savings', 'Savings Account'),
        ('current', 'Current Account'),
        ('salary', 'Salary Account'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_accounts')
    account_number = models.CharField(max_length=20, unique=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='savings')
    currency = models.CharField(max_length=10, default='INR')
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    available_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    is_primary = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_account_type_display()} - {self.account_number} ({self.user.username})"

    @property
    def formatted_current_balance(self):
        return format_inr(self.current_balance)

    @property
    def formatted_available_balance(self):
        return format_inr(self.available_balance)

    @property
    def masked_account_number(self):
        if len(self.account_number) >= 4:
            return f"•••• {self.account_number[-4:]}"
        return self.account_number


class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]

    CATEGORY_CHOICES = [
        ('shopping', 'Shopping'),
        ('salary', 'Income & Salary'),
        ('utilities', 'Bill Payment'),
        ('transfer', 'Transfer'),
        ('deposit', 'Deposit'),
        ('withdrawal', 'Cash Withdrawal'),
        ('dining', 'Food & Dining'),
        ('entertainment', 'Entertainment'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    reference_id = models.CharField(max_length=40, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    balance_after = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} | {self.transaction_type.upper()} | {self.amount}"

    @property
    def formatted_amount(self):
        sign = "+" if self.transaction_type == 'credit' else "-"
        return f"{sign}{format_inr(self.amount)}"

    @property
    def display_amount_class(self):
        return "text-emerald-600 dark:text-emerald-400" if self.transaction_type == 'credit' else "text-rose-600 dark:text-rose-400"

    @property
    def category_icon(self):
        icons = {
            'shopping': 'shopping-bag',
            'salary': 'arrow-down-left',
            'utilities': 'zap',
            'transfer': 'arrow-up-right',
            'deposit': 'plus-circle',
            'withdrawal': 'minus-circle',
            'dining': 'coffee',
            'entertainment': 'film',
            'other': 'credit-card',
        }
        return icons.get(self.category, 'credit-card')


class DebitCard(models.Model):
    CARD_TYPE_CHOICES = [
        ('debit', 'Debit Card'),
        ('credit', 'Credit Card'),
    ]

    NETWORK_CHOICES = [
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('rupay', 'RuPay'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='cards')
    card_number = models.CharField(max_length=25)  # e.g. "4532 8921 7392 4821"
    card_holder_name = models.CharField(max_length=100)
    card_type = models.CharField(max_length=20, choices=CARD_TYPE_CHOICES, default='debit')
    network = models.CharField(max_length=20, choices=NETWORK_CHOICES, default='visa')
    expiry_month = models.PositiveSmallIntegerField(default=12)
    expiry_year = models.PositiveSmallIntegerField(default=2030)
    cvv = models.CharField(max_length=4, default='842')
    is_active = models.BooleanField(default=True)
    is_frozen = models.BooleanField(default=False)
    daily_limit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('50000.00'))
    contactless_enabled = models.BooleanField(default=True)
    international_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.card_holder_name} - {self.last4} ({self.network.upper()})"

    @property
    def last4(self):
        clean = self.card_number.replace(" ", "")
        return clean[-4:] if len(clean) >= 4 else "0000"

    @property
    def masked_number(self):
        return f"•••• {self.last4}"

    @property
    def full_masked(self):
        return f"•••• •••• •••• {self.last4}"

    @property
    def expiry_display(self):
        return f"{self.expiry_month:02d}/{str(self.expiry_year)[-2:]}"

    @property
    def formatted_limit(self):
        return format_inr(self.daily_limit)


class Loan(models.Model):
    LOAN_TYPE_CHOICES = [
        ('personal', 'Personal Loan'),
        ('home', 'Home Loan'),
        ('auto', 'Auto Loan'),
        ('education', 'Education Loan'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('pending', 'Pending Approval'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    loan_type = models.CharField(max_length=30, choices=LOAN_TYPE_CHOICES, default='personal')
    account_number = models.CharField(max_length=30, unique=True)
    principal_amount = models.DecimalField(max_digits=15, decimal_places=2)
    remaining_amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.50'))
    tenure_months = models.PositiveIntegerField(default=36)
    monthly_emi = models.DecimalField(max_digits=12, decimal_places=2)
    next_due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_loan_type_display()} - {self.user.username} ({format_inr(self.remaining_amount)})"

    @property
    def formatted_remaining(self):
        return format_inr(self.remaining_amount)

    @property
    def formatted_principal(self):
        return format_inr(self.principal_amount)

    @property
    def formatted_emi(self):
        return format_inr(self.monthly_emi)

    @property
    def progress_percentage(self):
        if not self.principal_amount or self.principal_amount <= 0:
            return 0
        repaid = self.principal_amount - self.remaining_amount
        pct = (repaid / self.principal_amount) * 100
        return max(0, min(100, int(round(pct))))

    @property
    def repaid_amount(self):
        return self.principal_amount - self.remaining_amount

    @property
    def formatted_repaid(self):
        return format_inr(self.repaid_amount)


class Beneficiary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='beneficiaries')
    name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=30)
    bank_name = models.CharField(max_length=100, default='OMOM Bank')
    ifsc_code = models.CharField(max_length=20, default='OMOM0001234')
    nickname = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.nickname or self.bank_name})"


class SupportTicket(models.Model):
    CATEGORY_CHOICES = [
        ('account', 'Account & KYC'),
        ('cards', 'Card Services & PIN'),
        ('transfer', 'Transfer & Payments'),
        ('loans', 'Loan Inquiries'),
        ('security', 'Security & Fraud Report'),
        ('general', 'General Support'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    ticket_id = models.CharField(max_length=25, unique=True)
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default='general')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ticket_id} - {self.subject} ({self.status})"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('transaction', 'Transaction Alert'),
        ('security', 'Security Alert'),
        ('offer', 'Special Offer'),
        ('system', 'System Update'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='transaction')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.user.username})"
