from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import random
from .forms import LoginForm

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = LoginForm()
        
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def profile_view(request):
    return render(request, 'profile.html')

@login_required
def password_change_step1(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        if request.user.check_password(old_password):
            # Generate 6-digit OTP
            otp = str(random.randint(100000, 999999))
            request.session['pwd_change_otp'] = otp
            request.session['pwd_change_verified'] = False
            
            # Send Email
            subject = 'TIC MATRIX - Security Verification Code'
            message = f'Hello {request.user.name},\n\nYou have requested to change your password. Your verification code is: {otp}\n\nIf you did not request this, please contact your administrator immediately.\n\nThank you,\nTIC MATRIX Security Team'
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [request.user.email])
            
            return redirect('password_change_step2')
        else:
            messages.error(request, 'Incorrect current password.')
            
    return render(request, 'password_change_step1.html')

@login_required
def password_change_step2(request):
    if 'pwd_change_otp' not in request.session:
        return redirect('password_change_step1')
        
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        if entered_otp == request.session['pwd_change_otp']:
            request.session['pwd_change_verified'] = True
            return redirect('password_change_step3')
        else:
            messages.error(request, 'Invalid verification code.')
            
    return render(request, 'password_change_step2.html')

@login_required
def password_change_step3(request):
    if not request.session.get('pwd_change_verified'):
        return redirect('password_change_step1')
        
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password and new_password == confirm_password:
            # Update password
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user) # Keep user logged in
            
            # Cleanup session setup
            if 'pwd_change_otp' in request.session:
                del request.session['pwd_change_otp']
            if 'pwd_change_verified' in request.session:
                del request.session['pwd_change_verified']
                
            return redirect('profile')
        else:
            messages.error(request, 'Passwords do not match or are empty.')
            
    return render(request, 'password_change_step3.html')
