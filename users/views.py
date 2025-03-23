from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from social_django.utils import load_strategy, load_backend
from social_core.exceptions import MissingBackend, AuthFailed
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from social_django.models import UserSocialAuth


def home_view(request):
    """View for the home page that redirects to login if not authenticated."""
    if request.user.is_authenticated:
        # Get a valid user to chat with or redirect to the first available user
        other_users = User.objects.exclude(id=request.user.id)
        if other_users.exists():
            return redirect(f'/chat/{other_users.first().username}/')
        else:
            # If no other users, redirect to their own chat (for UI display)
            return redirect(f'/chat/{request.user.username}/')
    else:
        return redirect('login')







def login_view(request):
    if request.user.is_authenticated:
        # Reuse the same redirection logic as home_view
        other_users = User.objects.exclude(id=request.user.id)
        if other_users.exists():
            return redirect(f'/chat/{other_users.first().username}/')
        else:
            return redirect(f'/chat/{request.user.username}/')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            # Redirect to chat with another user or self
            other_users = User.objects.exclude(id=user.id)
            if other_users.exists():
                return redirect(f'/chat/{other_users.first().username}/')
            else:
                return redirect(f'/chat/{user.username}/')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')

def register_view(request):
    if request.user.is_authenticated:
        # Reuse the same redirection logic
        other_users = User.objects.exclude(id=request.user.id)
        if other_users.exists():
            return redirect(f'/chat/{other_users.first().username}/')
        else:
            return redirect(f'/chat/{request.user.username}/')

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
            # Redirect to chat with another user or self
            other_users = User.objects.exclude(id=user.id)
            if other_users.exists():
                return redirect(f'/chat/{other_users.first().username}/')
            else:
                return redirect(f'/chat/{user.username}/')
        except Exception as e:
            messages.error(request, str(e))

    return render(request, 'register.html')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_auth_token(request):
    """Get or create an authentication token for the current user."""
    token, created = Token.objects.get_or_create(user=request.user)
    return Response({'token': token.key})


@api_view(['POST'])
@permission_classes([AllowAny])
def obtain_auth_token(request):
    """API endpoint that accepts username/email and password and returns an auth token."""
    username = request.data.get('username')
    password = request.data.get('password')

    # Check if username is actually an email
    if '@' in username:
        try:
            user = User.objects.get(email=username)
            username = user.username
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    # Try to find the user
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    # First try standard authentication
    authenticated_user = authenticate(username=username, password=password)

    if authenticated_user:
        # Standard authentication succeeded
        token, created = Token.objects.get_or_create(user=authenticated_user)
        return Response({'token': token.key}, status=status.HTTP_200_OK)
    else:
        # Check if this is a social auth user (Google OAuth)
        try:
            # Check if user has a social auth account
            social_auth = UserSocialAuth.objects.get(user=user)
            if social_auth.provider == 'google-oauth2':
                # This is a Google OAuth user, create a token
                token, created = Token.objects.get_or_create(user=user)
                return Response({'token': token.key}, status=status.HTTP_200_OK)
        except UserSocialAuth.DoesNotExist:
            # Not a social auth user
            pass

        # If we get here, authentication failed
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
