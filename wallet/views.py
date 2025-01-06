from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Wallet, Transaction, WithdrawalRequest
from .forms import WithdrawalForm
from django.contrib import messages
from decimal import Decimal 
from django.contrib import admin
from django.conf import settings
from userProfile.models import UserProfile
from django.core.mail import EmailMessage
from django.core.mail import send_mail
import threading
from django.http import HttpResponseRedirect
from django.urls import reverse

class EmailThread(threading.Thread):
    def __init__(self, email_subject, email_body, from_email, recipient_list):
        self.email_subject = email_subject
        self.email_body = email_body
        self.from_email = from_email
        self.recipient_list = recipient_list
        threading.Thread.__init__(self)

    def run(self):
        send_mail(self.email_subject, self.email_body, self.from_email, self.recipient_list)



def wallet_dashboard(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)  # Get or create a wallet for the user
    transactions = wallet.transactions.all()  # Get all wallet transactions

    user_requests = WithdrawalRequest.objects.filter(user=request.user)
    return render(request, 'wallet/dashboard.html', {
        'wallet': wallet,
        'transactions': transactions,
        'user_requests': user_requests,
    })


def add_funds(request):
    user = request.user if request.user.is_authenticated else get_demo_user()
    wallet, created = Wallet.objects.get_or_create(user=user)
    user_profile = UserProfile.objects.get(user=request.user)
    recipient = user_profile.email
    print(recipient)
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))  # Convert the input to Decimal
        except (ValueError, InvalidOperation):
            amount = Decimal(0)  # Handle invalid input

        if amount > 0:
            # Add funds to the wallet (both are Decimals now)
            wallet.balance += amount
            wallet.save()

            # Record a transaction
            Transaction.objects.create(wallet=wallet, transaction_type='DEPOSIT', amount=amount)
            email_subject = 'SmartSpend Wallet'
            amount = str(amount)
            email_body = 'Hi '+ user.username +' You have deposited amount Rs.'+amount+' to your SmartSpend Wallet.\n The amount will be credited to your Wallet within 2 hours.\n Thank you'
            
            from_email = settings.EMAIL_HOST_USER
            email = recipient
            recipient_list = [email]
            #send_mail(email_subject,email_body,from_email,recipient_list)
            email_thread = EmailThread(email_subject, email_body, from_email, recipient_list)
            email_thread.start()

            messages.success(request, f"Successfully added {amount} to the wallet!")
            url = reverse('wallet_dashboard')  # Reverse lookup for the wallet dashboard URL
            query_string = '?success=true'
            return HttpResponseRedirect(f"{url}{query_string}")

    return render(request, 'wallet/add_funds.html')


def fund_success(request):
    return render(request, 'fund_success.html')

def withdrawal_request_view(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        reason = request.POST.get('reason')
        wallet = Wallet.objects.get(user=request.user)

        user = request.user
        user_profile = UserProfile.objects.get(user=request.user)
        recipient = user_profile.email

        # Check if the requested amount is greater than the available balance
        if wallet.balance >= float(amount):
            # Create a withdrawal request
            withdrawal_request = WithdrawalRequest.objects.create(
                user=request.user,
                amount=amount,
                reason=reason,
            )
            email_subject = 'Withdrawal Request'
            email_body = 'Hi '+ user.username +' You have requested a withdrawal of amount Rs.'+amount+' from your SmartSpend Wallet.\n The amount will be credited to your account within 2 hours.\n Thank you'
            
            from_email = settings.EMAIL_HOST_USER
            email = recipient
            recipient_list = [email]
            #send_mail(email_subject,email_body,from_email,recipient_list)
            email_thread = EmailThread(email_subject, email_body, from_email, recipient_list)
            email_thread.start()
            messages.success(request, 'Withdrawal request submitted successfully.')
            return redirect('withdraw_funds')
        else:
            messages.error(request, 'Insufficient funds for this withdrawal request.')

    # Fetch the user's withdrawal requests
    user_requests = WithdrawalRequest.objects.filter(user=request.user)
    return render(request, 'wallet/withdrawal_funds.html', {'user_requests': user_requests})