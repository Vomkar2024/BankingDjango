from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import CustomerProfile
from dashboard.models import Account, Transaction, DebitCard, Loan, Beneficiary, SupportTicket, Notification


class Command(BaseCommand):
    help = "Seeds database with realistic banking data for demo and testing"

    def handle(self, *args, **options):
        self.stdout.write("Starting banking seed data creation...")

        # 1. Superuser / Admin
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@omombank.com',
                'first_name': 'Bank',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('Admin@12345')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

        # 2. Demo User: Alex Morgan
        alex, created = User.objects.get_or_create(
            username='alex',
            defaults={
                'email': 'alex.morgan@omombank.com',
                'first_name': 'Alex',
                'last_name': 'Morgan',
            }
        )
        alex.set_password('Alex@12345')
        alex.first_name = 'Alex'
        alex.last_name = 'Morgan'
        alex.email = 'alex.morgan@omombank.com'
        alex.save()

        # Profile
        profile, _ = CustomerProfile.objects.get_or_create(user=alex)
        profile.phone_number = '+91 98201 44521'
        profile.pan_number = 'ALEXM7892K'
        profile.aadhaar_last4 = '4821'
        profile.address = 'Flat 14B, Skyview Towers, Bandra Kurla Complex'
        profile.city = 'Mumbai'
        profile.state = 'Maharashtra'
        profile.pincode = '400051'
        profile.kyc_status = 'verified'
        profile.account_tier = 'platinum'
        profile.save()

        # 3. Bank Accounts
        # Primary Savings Account
        savings_acc, _ = Account.objects.get_or_create(
            user=alex,
            account_number='409281729012',
            defaults={
                'account_type': 'savings',
                'currency': 'INR',
                'current_balance': Decimal('125450.00'),
                'available_balance': Decimal('118200.00'),
                'is_primary': True,
                'is_active': True,
            }
        )
        savings_acc.current_balance = Decimal('125450.00')
        savings_acc.available_balance = Decimal('118200.00')
        savings_acc.save()

        # Secondary Current Account
        current_acc, _ = Account.objects.get_or_create(
            user=alex,
            account_number='889102938102',
            defaults={
                'account_type': 'current',
                'currency': 'INR',
                'current_balance': Decimal('42500.00'),
                'available_balance': Decimal('42500.00'),
                'is_primary': False,
                'is_active': True,
            }
        )

        # 4. Debit & Credit Cards
        # Debit Card (Visa - ending in 4821)
        DebitCard.objects.filter(account=savings_acc).delete()
        debit_card = DebitCard.objects.create(
            account=savings_acc,
            card_number='4532 8921 7392 4821',
            card_holder_name='ALEX MORGAN',
            card_type='debit',
            network='visa',
            expiry_month=8,
            expiry_year=2029,
            cvv='482',
            is_active=True,
            is_frozen=False,
            daily_limit=Decimal('50000.00'),
            contactless_enabled=True,
            international_enabled=True,
        )

        # Credit Card (Mastercard)
        credit_card = DebitCard.objects.create(
            account=savings_acc,
            card_number='5412 7539 0182 9104',
            card_holder_name='ALEX MORGAN',
            card_type='credit',
            network='mastercard',
            expiry_month=11,
            expiry_year=2028,
            cvv='910',
            is_active=True,
            is_frozen=False,
            daily_limit=Decimal('150000.00'),
            contactless_enabled=True,
            international_enabled=False,
        )

        # 5. Loan
        Loan.objects.filter(user=alex).delete()
        personal_loan = Loan.objects.create(
            user=alex,
            loan_type='personal',
            account_number='LN-PL-783921',
            principal_amount=Decimal('500000.00'),
            remaining_amount=Decimal('350000.00'),
            interest_rate=Decimal('10.50'),
            tenure_months=36,
            monthly_emi=Decimal('14600.00'),
            next_due_date=timezone.now().date() + timedelta(days=7),
            status='active',
        )

        # 6. Transactions
        Transaction.objects.filter(account=savings_acc).delete()
        now = timezone.now()

        transactions_data = [
            {
                'type': 'debit',
                'category': 'shopping',
                'title': 'Amazon',
                'description': 'Electronics & Books Online Store',
                'amount': Decimal('2450.00'),
                'ref': 'TXN9820260101',
                'time_delta': timedelta(hours=3),
                'balance': Decimal('125450.00'),
            },
            {
                'type': 'credit',
                'category': 'salary',
                'title': 'Salary',
                'description': 'TechCorp Systems Monthly Pay',
                'amount': Decimal('75000.00'),
                'ref': 'TXN9820260102',
                'time_delta': timedelta(days=1, hours=4),
                'balance': Decimal('127900.00'),
            },
            {
                'type': 'debit',
                'category': 'utilities',
                'title': 'Electricity',
                'description': 'Adani Electricity Mumbai Monthly Bill',
                'amount': Decimal('1250.00'),
                'ref': 'TXN9820260103',
                'time_delta': timedelta(days=2, hours=1),
                'balance': Decimal('52900.00'),
            },
            {
                'type': 'debit',
                'category': 'dining',
                'title': 'Swiggy Gourmet',
                'description': 'Artisanal Cafe Order #82910',
                'amount': Decimal('680.00'),
                'ref': 'TXN9820260104',
                'time_delta': timedelta(days=3, hours=5),
                'balance': Decimal('54150.00'),
            },
            {
                'type': 'debit',
                'category': 'entertainment',
                'title': 'Netflix Premium',
                'description': 'Monthly 4K Subscription',
                'amount': Decimal('649.00'),
                'ref': 'TXN9820260105',
                'time_delta': timedelta(days=4, hours=2),
                'balance': Decimal('54830.00'),
            },
            {
                'type': 'debit',
                'category': 'transfer',
                'title': 'Priya Sharma',
                'description': 'Weekend trip shared split transfer',
                'amount': Decimal('5000.00'),
                'ref': 'TXN9820260106',
                'time_delta': timedelta(days=5, hours=8),
                'balance': Decimal('55479.00'),
            },
            {
                'type': 'credit',
                'category': 'salary',
                'title': 'Freelance Advisory',
                'description': 'Fintech Design Sprint Consulting',
                'amount': Decimal('28500.00'),
                'ref': 'TXN9820260107',
                'time_delta': timedelta(days=7, hours=3),
                'balance': Decimal('60479.00'),
            },
            {
                'type': 'debit',
                'category': 'utilities',
                'title': 'HP Petrol Pump',
                'description': 'Fuel refill - Premium Speed',
                'amount': Decimal('3200.00'),
                'ref': 'TXN9820260108',
                'time_delta': timedelta(days=9, hours=6),
                'balance': Decimal('31979.00'),
            },
            {
                'type': 'debit',
                'category': 'shopping',
                'title': 'Apple Store BKC',
                'description': 'MagSafe Accessories',
                'amount': Decimal('4900.00'),
                'ref': 'TXN9820260109',
                'time_delta': timedelta(days=11, hours=7),
                'balance': Decimal('35179.00'),
            },
            {
                'type': 'credit',
                'category': 'deposit',
                'title': 'Quarterly Interest',
                'description': 'Savings Account Q3 Interest Credit',
                'amount': Decimal('1120.00'),
                'ref': 'TXN9820260110',
                'time_delta': timedelta(days=14, hours=1),
                'balance': Decimal('40079.00'),
            },
        ]

        for item in transactions_data:
            Transaction.objects.create(
                account=savings_acc,
                transaction_type=item['type'],
                category=item['category'],
                title=item['title'],
                description=item['description'],
                amount=item['amount'],
                reference_id=item['ref'],
                status='completed',
                balance_after=item['balance'],
                created_at=now - item['time_delta'],
            )

        # 7. Beneficiaries
        Beneficiary.objects.filter(user=alex).delete()
        Beneficiary.objects.create(
            user=alex,
            name='Priya Sharma',
            account_number='029103948192',
            bank_name='HDFC Bank',
            ifsc_code='HDFC0001048',
            nickname='Priya S.'
        )
        Beneficiary.objects.create(
            user=alex,
            name='Rohan Verma',
            account_number='309182749102',
            bank_name='State Bank of India',
            ifsc_code='SBIN0004921',
            nickname='Rohan Colleague'
        )
        Beneficiary.objects.create(
            user=alex,
            name='Apex Residency Maintenance',
            account_number='409281729055',
            bank_name='OMOM Bank',
            ifsc_code='OMOM0001234',
            nickname='Society Dues'
        )

        # 8. Notifications
        Notification.objects.filter(user=alex).delete()
        Notification.objects.create(
            user=alex,
            title='Salary Credited: ₹75,000.00',
            message='Your salary from TechCorp Systems for this month has been credited to A/C •••• 9012.',
            notification_type='transaction',
            is_read=False,
        )
        Notification.objects.create(
            user=alex,
            title='EMI Reminder: Personal Loan',
            message='Your upcoming EMI of ₹14,600.00 for Personal Loan LN-PL-783921 is due in 7 days.',
            notification_type='system',
            is_read=False,
        )
        Notification.objects.create(
            user=alex,
            title='Security Alert',
            message='Successful login detected from Chrome (Windows) in Mumbai, India.',
            notification_type='security',
            is_read=True,
        )

        # 9. Support Tickets
        SupportTicket.objects.filter(user=alex).delete()
        SupportTicket.objects.create(
            user=alex,
            ticket_id='SUP-2026-9041',
            category='cards',
            subject='International POS transaction limit increase inquiry',
            message='I will be traveling next month and would like to understand card limit adjustments.',
            status='resolved',
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded banking database!"))
        self.stdout.write(self.style.SUCCESS("Demo User: alex | Password: Alex@12345"))
        self.stdout.write(self.style.SUCCESS("Admin User: admin | Password: Admin@12345"))
