from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from social_django.utils import load_strategy, load_backend
from social_core.exceptions import MissingBackend, AuthFailed



def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username)
        print(password)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('/chat/Ammar/')
        else:
            messages.error(request, 'Invalid email or password. Please try again.')
    if request.user.is_authenticated:
        return redirect('/chat/Ammar/')
    return render(request,'login.html')


@login_required
def logout_page(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('/')


def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password1 = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Check if passwords match
        if password1 != confirm_password:
            messages.error(request, 'Passwords do not match. Please try again.')
            return render(request, 'signup.html')

        # Check if email is already taken
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already in use. Please try another.')
            return render(request, 'signup.html')

        # Create the new user
        user = User.objects.create_user(username=username,
                                        email=email,
                                        password=password1
                                        )
        user.save()
        messages.success(request, 'Signup successful! You can now log in.')
        return redirect('login')
    if request.user.is_authenticated:
        return redirect('/chat/Ammar/') #todo: pass usename
    return render(request, 'signup.html')




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






@login_required
def custom_logout(request):
    logout(request)
    return redirect('login')



