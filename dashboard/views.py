import csv
import json
import random
from decimal import Decimal
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Q

from .models import Account, Transaction, DebitCard, Loan, Beneficiary, SupportTicket, Notification, format_inr


def get_greeting():
    """Returns dynamic time-appropriate greeting"""
    current_hour = timezone.localtime(timezone.now()).hour
    if current_hour < 12:
        return "Good morning"
    elif current_hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


@login_required
def dashboard_view(request):
    user = request.user
    
    # 1. Primary Account (or create default if somehow missing)
    primary_account = Account.objects.filter(user=user, is_active=True, is_primary=True).first()
    if not primary_account:
        primary_account = Account.objects.filter(user=user, is_active=True).first()
    if not primary_account:
        primary_account = Account.objects.create(
            user=user,
            account_number=f"409{random.randint(100000000, 999999999)}",
            account_type='savings',
            currency='INR',
            current_balance=Decimal('10000.00'),
            available_balance=Decimal('10000.00'),
            is_primary=True,
            is_active=True,
        )

    # 2. All accounts of user
    all_accounts = Account.objects.filter(user=user, is_active=True)

    # 3. Transactions for current primary account (or all user accounts)
    transactions = (
        Transaction.objects.filter(account=primary_account)
        .order_by('-created_at')[:10]
    )

    # 4. Monthly metrics calculation
    first_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_income = (
        Transaction.objects.filter(
            account=primary_account,
            transaction_type='credit',
            status='completed',
            created_at__gte=first_of_month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    )
    month_expense = (
        Transaction.objects.filter(
            account=primary_account,
            transaction_type='debit',
            status='completed',
            created_at__gte=first_of_month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    )

    # 5. Cards for active accounts
    cards = DebitCard.objects.filter(account__in=all_accounts, is_active=True).order_by('-created_at')

    # 6. Active Loans
    loans = Loan.objects.filter(user=user, status='active').order_by('-created_at')

    # 7. Beneficiaries
    beneficiaries = Beneficiary.objects.filter(user=user).order_by('name')

    # 8. Unread notifications
    notifications = Notification.objects.filter(user=user).order_by('-created_at')[:5]
    unread_count = Notification.objects.filter(user=user, is_read=False).count()

    # 9. Recent support tickets
    tickets = SupportTicket.objects.filter(user=user).order_by('-created_at')[:3]

    # 10. Spending category breakdown for chart
    categories_agg = (
        Transaction.objects.filter(
            account=primary_account,
            transaction_type='debit',
            status='completed'
        ).values('category').annotate(total=Sum('amount')).order_by('-total')
    )
    chart_categories = [c['category'].title() for c in categories_agg[:5]]
    chart_amounts = [float(c['total']) for c in categories_agg[:5]]

    context = {
        'account': primary_account,
        'all_accounts': all_accounts,
        'transactions': transactions,
        'cards': cards,
        'loans': loans,
        'beneficiaries': beneficiaries,
        'notifications': notifications,
        'unread_count': unread_count,
        'tickets': tickets,
        'greeting': get_greeting(),
        'month_income': format_inr(month_income),
        'month_expense': format_inr(month_expense),
        'chart_categories_json': json.dumps(chart_categories),
        'chart_amounts_json': json.dumps(chart_amounts),
        'user_name': user.first_name or user.username,
    }
    return render(request, 'dashboard/index.html', context)


@login_required
def transfer_money(request):
    if request.method != 'POST':
        return redirect('dashboard')

    user = request.user
    account_id = request.POST.get('account_id')
    account = Account.objects.filter(id=account_id, user=user, is_active=True).first() if account_id else Account.objects.filter(user=user, is_primary=True).first()

    if not account:
        messages.error(request, "Primary account not found.")
        return redirect('dashboard')

    recipient = request.POST.get('recipient', '').strip()
    target_account_number = request.POST.get('target_account_number', '').strip()
    amount_str = request.POST.get('amount', '0').strip()
    notes = request.POST.get('notes', 'Funds Transfer').strip()

    try:
        amount = Decimal(amount_str)
        if amount <= Decimal('0.00'):
            raise ValueError()
    except Exception:
        messages.error(request, "Please enter a valid transfer amount greater than ₹0.")
        return redirect('dashboard')

    if amount > account.available_balance:
        messages.error(request, f"Insufficient available balance. Your balance is {account.formatted_available_balance}.")
        return redirect('dashboard')

    try:
        with transaction.atomic():
            # Deduct balance
            account.current_balance -= amount
            account.available_balance -= amount
            account.save()

            ref_id = f"TRF{random.randint(1000000000, 9999999999)}"
            # Sender Debit Transaction
            Transaction.objects.create(
                account=account,
                transaction_type='debit',
                category='transfer',
                title=f"Transfer to {recipient or target_account_number or 'Beneficiary'}",
                description=notes or "Online Transfer",
                amount=amount,
                reference_id=ref_id,
                status='completed',
                balance_after=account.current_balance,
            )

            # Check if internal recipient exists
            if target_account_number:
                recipient_acc = Account.objects.filter(account_number=target_account_number, is_active=True).first()
                if recipient_acc and recipient_acc != account:
                    recipient_acc.current_balance += amount
                    recipient_acc.available_balance += amount
                    recipient_acc.save()

                    Transaction.objects.create(
                        account=recipient_acc,
                        transaction_type='credit',
                        category='transfer',
                        title=f"Transfer from {user.get_full_name() or user.username}",
                        description=notes or "Online Inward Transfer",
                        amount=amount,
                        reference_id=f"REV{ref_id}",
                        status='completed',
                        balance_after=recipient_acc.current_balance,
                    )
                    Notification.objects.create(
                        user=recipient_acc.user,
                        title=f"Money Received: {format_inr(amount)}",
                        message=f"Received {format_inr(amount)} from {user.get_full_name() or user.username}. Ref: {ref_id}",
                        notification_type='transaction'
                    )

            # Notification to sender
            Notification.objects.create(
                user=user,
                title=f"Transfer Successful: {format_inr(amount)}",
                message=f"Successfully transferred {format_inr(amount)} to {recipient or target_account_number}. Ref: {ref_id}",
                notification_type='transaction'
            )

            messages.success(request, f"Successfully transferred {format_inr(amount)} to {recipient or target_account_number}! Ref: {ref_id}")
    except Exception as e:
        messages.error(request, f"Transfer failed: {str(e)}")

    return redirect('dashboard')


@login_required
def pay_bill(request):
    if request.method != 'POST':
        return redirect('dashboard')

    user = request.user
    account = Account.objects.filter(user=user, is_primary=True, is_active=True).first()
    if not account:
        account = Account.objects.filter(user=user, is_active=True).first()

    biller_type = request.POST.get('biller_type', 'Electricity')
    biller_name = request.POST.get('biller_name', 'Utility Provider').strip()
    consumer_id = request.POST.get('consumer_id', '').strip()
    amount_str = request.POST.get('amount', '0').strip()

    try:
        amount = Decimal(amount_str)
        if amount <= Decimal('0.00'):
            raise ValueError()
    except Exception:
        messages.error(request, "Please enter a valid bill amount greater than ₹0.")
        return redirect('dashboard')

    if amount > account.available_balance:
        messages.error(request, f"Insufficient balance to pay this bill. Current balance: {account.formatted_available_balance}.")
        return redirect('dashboard')

    try:
        with transaction.atomic():
            account.current_balance -= amount
            account.available_balance -= amount
            account.save()

            ref_id = f"BIL{random.randint(1000000000, 9999999999)}"
            Transaction.objects.create(
                account=account,
                transaction_type='debit',
                category='utilities',
                title=biller_name or f"{biller_type} Bill",
                description=f"{biller_type} payment for Consumer ID: {consumer_id or 'Auto'}",
                amount=amount,
                reference_id=ref_id,
                status='completed',
                balance_after=account.current_balance,
            )

            Notification.objects.create(
                user=user,
                title=f"Bill Paid: {biller_name} ({format_inr(amount)})",
                message=f"Your {biller_type} bill of {format_inr(amount)} to {biller_name} was paid successfully. Ref: {ref_id}",
                notification_type='transaction'
            )

            messages.success(request, f"Bill payment of {format_inr(amount)} to {biller_name} was successful! Ref: {ref_id}")
    except Exception as e:
        messages.error(request, f"Bill payment failed: {str(e)}")

    return redirect('dashboard')


@login_required
def deposit_funds(request):
    if request.method != 'POST':
        return redirect('dashboard')

    user = request.user
    account = Account.objects.filter(user=user, is_primary=True, is_active=True).first()
    amount_str = request.POST.get('amount', '0').strip()
    source = request.POST.get('source', 'UPI / NetBanking')

    try:
        amount = Decimal(amount_str)
        if amount <= Decimal('0.00'):
            raise ValueError()
    except Exception:
        messages.error(request, "Please enter a valid deposit amount.")
        return redirect('dashboard')

    try:
        with transaction.atomic():
            account.current_balance += amount
            account.available_balance += amount
            account.save()

            ref_id = f"DEP{random.randint(1000000000, 9999999999)}"
            Transaction.objects.create(
                account=account,
                transaction_type='credit',
                category='deposit',
                title=f"Deposit via {source}",
                description=f"Instant funds deposit into {account.masked_account_number}",
                amount=amount,
                reference_id=ref_id,
                status='completed',
                balance_after=account.current_balance,
            )

            Notification.objects.create(
                user=user,
                title=f"Deposit Success: {format_inr(amount)}",
                message=f"Your account has been credited with {format_inr(amount)} via {source}. Ref: {ref_id}",
                notification_type='transaction'
            )

            messages.success(request, f"Deposit of {format_inr(amount)} credited successfully! Updated balance: {account.formatted_current_balance}")
    except Exception as e:
        messages.error(request, f"Deposit failed: {str(e)}")

    return redirect('dashboard')


@login_required
def withdraw_funds(request):
    if request.method != 'POST':
        return redirect('dashboard')

    user = request.user
    account = Account.objects.filter(user=user, is_primary=True, is_active=True).first()
    amount_str = request.POST.get('amount', '0').strip()
    method = request.POST.get('method', 'ATM Cardless Cash')

    try:
        amount = Decimal(amount_str)
        if amount <= Decimal('0.00'):
            raise ValueError()
    except Exception:
        messages.error(request, "Please enter a valid withdrawal amount.")
        return redirect('dashboard')

    if amount > account.available_balance:
        messages.error(request, f"Insufficient balance for withdrawal. Available: {account.formatted_available_balance}")
        return redirect('dashboard')

    try:
        with transaction.atomic():
            account.current_balance -= amount
            account.available_balance -= amount
            account.save()

            ref_id = f"WTH{random.randint(1000000000, 9999999999)}"
            otp_pin = random.randint(100000, 999999)
            Transaction.objects.create(
                account=account,
                transaction_type='debit',
                category='withdrawal',
                title=f"Cash Withdrawal ({method})",
                description=f"Withdrawal authorization OTP generated. Valid for 15 mins.",
                amount=amount,
                reference_id=ref_id,
                status='completed',
                balance_after=account.current_balance,
            )

            Notification.objects.create(
                user=user,
                title=f"Withdrawal Approved: {format_inr(amount)}",
                message=f"Cash withdrawal OTP: {otp_pin}. Use this OTP at any OMOM Bank ATM. Ref: {ref_id}",
                notification_type='security'
            )

            messages.success(request, f"Withdrawal request of {format_inr(amount)} approved! Your ATM Cash OTP is {otp_pin} (valid 15 minutes). Ref: {ref_id}")
    except Exception as e:
        messages.error(request, f"Withdrawal failed: {str(e)}")

    return redirect('dashboard')


@login_required
def toggle_card_freeze(request, card_id):
    if request.method == 'POST':
        card = get_object_or_404(DebitCard, id=card_id, account__user=request.user)
        card.is_frozen = not card.is_frozen
        card.save()

        status_text = "locked / frozen" if card.is_frozen else "unlocked & active"
        messages.info(request, f"Card ending in {card.last4} is now {status_text}.")
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok', 'is_frozen': card.is_frozen, 'message': f"Card is now {status_text}."})

    return redirect('dashboard')


@login_required
def toggle_contactless(request, card_id):
    if request.method == 'POST':
        card = get_object_or_404(DebitCard, id=card_id, account__user=request.user)
        card.contactless_enabled = not card.contactless_enabled
        card.save()

        state = "enabled" if card.contactless_enabled else "disabled"
        messages.info(request, f"Contactless payments {state} for card ending in {card.last4}.")

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok', 'contactless': card.contactless_enabled})

    return redirect('dashboard')


@login_required
def create_ticket(request):
    if request.method == 'POST':
        user = request.user
        category = request.POST.get('category', 'general')
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if not subject or not message:
            messages.error(request, "Please enter both subject and message for your support ticket.")
            return redirect('dashboard')

        ticket_id = f"SUP-{timezone.now().year}-{random.randint(1000, 9999)}"
        SupportTicket.objects.create(
            user=user,
            ticket_id=ticket_id,
            category=category,
            subject=subject,
            message=message,
            status='open',
        )

        Notification.objects.create(
            user=user,
            title=f"Support Ticket Created: {ticket_id}",
            message=f"Our 24x7 customer support team has received your ticket regarding '{subject}'. An executive will respond shortly.",
            notification_type='system',
        )

        messages.success(request, f"Support ticket #{ticket_id} submitted successfully! Our representative will respond within 2 hours.")
    return redirect('dashboard')


@login_required
def mark_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok'})
        messages.success(request, "All notifications marked as read.")
    return redirect('dashboard')


@login_required
def transactions_view(request):
    user = request.user
    accounts = Account.objects.filter(user=user, is_active=True)
    
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    txn_type = request.GET.get('type', '')

    txns = Transaction.objects.filter(account__in=accounts)

    if query:
        txns = txns.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(reference_id__icontains=query))
    if category:
        txns = txns.filter(category=category)
    if txn_type:
        txns = txns.filter(transaction_type=txn_type)

    txns = txns.order_by('-created_at')

    # Export to CSV if requested
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="OMOM_Statement_{timezone.now().strftime("%Y%m%d")}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Reference ID', 'Title', 'Description', 'Category', 'Type', 'Amount (INR)', 'Balance After'])
        for t in txns:
            writer.writerow([t.created_at.strftime('%Y-%m-%d %H:%M'), t.reference_id, t.title, t.description, t.category, t.transaction_type, t.amount, t.balance_after])
        return response

    context = {
        'transactions': txns,
        'query': query,
        'selected_category': category,
        'selected_type': txn_type,
        'accounts': accounts,
    }
    return render(request, 'dashboard/transactions.html', context)


@login_required
def cards_view(request):
    user = request.user
    accounts = Account.objects.filter(user=user, is_active=True)
    cards = DebitCard.objects.filter(account__in=accounts)
    return render(request, 'dashboard/cards.html', {'cards': cards, 'accounts': accounts})


@login_required
def loans_view(request):
    user = request.user
    loans = Loan.objects.filter(user=user).order_by('-created_at')
    return render(request, 'dashboard/loans.html', {'loans': loans})


@login_required
def support_view(request):
    user = request.user
    tickets = SupportTicket.objects.filter(user=user).order_by('-created_at')
    return render(request, 'dashboard/support.html', {'tickets': tickets})
