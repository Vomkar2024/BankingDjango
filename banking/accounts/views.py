import random
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from .forms import LoginForm, RegisterForm
from dashboard.models import Account, DebitCard, Notification, Transaction


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        user = authenticate(request, username=username, password=password)
        if not user:
            # Check if username is actually an email
            try:
                user_obj = User.objects.get(email__iexact=username)
                user = authenticate(request, username=user_obj.username, password=password)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                user = None

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next') or 'dashboard'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please verify your credentials.")

    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.save()

                # Customer Profile
                profile = user.profile
                profile.phone_number = form.cleaned_data['phone_number']
                profile.kyc_status = 'verified'
                profile.account_tier = 'gold'
                profile.save()

                # Generate unique 12-digit account number
                acc_num = f"409{random.randint(100000000, 999999999)}"
                initial_deposit = Decimal('50000.00')

                # Create Primary Savings Account
                account = Account.objects.create(
                    user=user,
                    account_number=acc_num,
                    account_type='savings',
                    currency='INR',
                    current_balance=initial_deposit,
                    available_balance=initial_deposit,
                    is_primary=True,
                    is_active=True,
                )

                # Initial Welcome Credit Transaction
                ref_id = f"TXN{random.randint(1000000000, 9999999999)}"
                Transaction.objects.create(
                    account=account,
                    transaction_type='credit',
                    category='deposit',
                    title='Welcome Bonus Deposit',
                    description='OMOM Bank Account Opening Starter Credit',
                    amount=initial_deposit,
                    reference_id=ref_id,
                    status='completed',
                    balance_after=initial_deposit,
                )

                # Generate Virtual Debit Card
                card_part2 = f"{random.randint(1000, 9999)}"
                card_part3 = f"{random.randint(1000, 9999)}"
                card_part4 = f"{random.randint(1000, 9999)}"
                full_card = f"4532 {card_part2} {card_part3} {card_part4}"
                full_name = f"{user.first_name} {user.last_name}".strip().upper() or user.username.upper()

                DebitCard.objects.create(
                    account=account,
                    card_number=full_card,
                    card_holder_name=full_name,
                    card_type='debit',
                    network='visa',
                    expiry_month=12,
                    expiry_year=2030,
                    cvv=str(random.randint(100, 999)),
                    is_active=True,
                    is_frozen=False,
                    daily_limit=Decimal('50000.00'),
                    contactless_enabled=True,
                )

                # Welcome Notification
                Notification.objects.create(
                    user=user,
                    title='Welcome to OMOM Bank!',
                    message=f'Your new digital Savings Account {account.masked_account_number} is ready with a welcome credit of ₹50,000.00.',
                    notification_type='system',
                    is_read=False,
                )

                # Log user in
                login(request, user)
                messages.success(request, f"Account created successfully! Welcome to OMOM Bank, {user.first_name}!")
                return redirect('dashboard')
        except Exception as e:
            messages.error(request, f"An error occurred while creating your account: {str(e)}")

    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been safely signed out. See you soon!")
    return redirect('login')
