from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from social_django.utils import load_strategy, load_backend
from social_core.exceptions import MissingBackend, AuthFailed


def home_view(request):
    """View for the home page that redirects to login if not authenticated."""
    if request.user.is_authenticated:
        return redirect('/chat/Ammar/')
    else:
        return redirect('login')







def login_view(request):
    if request.user.is_authenticated:
       return redirect('/chat/Ammar/')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('/chat/Ammar/')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('/chat/Ammar/')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'register.html')

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=request.POST.get('first_name', ''),
                last_name=request.POST.get('last_name', '')
            )
            # تحديد الـ backend عند تسجيل الدخول
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('/chat/Ammar/')
        except Exception as e:
            messages.error(request, str(e))

    return render(request, 'register.html')








