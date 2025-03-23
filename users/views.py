from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from social_django.utils import load_strategy, load_backend
from social_core.exceptions import MissingBackend, AuthFailed
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken


def generate_tokens_for_user(user):
    """Generate JWT tokens for a user and return them as a dictionary."""
    refresh = RefreshToken.for_user(user)
    return {
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh)
    }


def generate_auth_token_for_user(user):
    """Generate or get an authentication token for a user."""
    token, created = Token.objects.get_or_create(user=user)
    return {
        'token': token.key
    }


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

            # Generate tokens for the user
            jwt_tokens = generate_tokens_for_user(user)
            auth_token = generate_auth_token_for_user(user)

            # Combine tokens
            tokens = {
                **jwt_tokens,
                **auth_token
            }

            # Check if this is an AJAX request or API request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json':
                other_users = User.objects.exclude(id=user.id)
                return JsonResponse({
                    'success': True,
                    'tokens': tokens,
                    'redirect_url': f'/chat/{other_users.first().username}/' if other_users.exists() else f'/chat/{user.username}/'
                })

            # For regular form submission, redirect to chat
            other_users = User.objects.exclude(id=user.id)
            if other_users.exists():
                return redirect(f'/chat/{other_users.first().username}/')
            else:
                return redirect(f'/chat/{user.username}/')
        else:
            messages.error(request, 'Invalid username or password.')

            # Return JSON response for API requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid username or password.'
                }, status=401)

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

            # Generate tokens for the user
            jwt_tokens = generate_tokens_for_user(user)
            auth_token = generate_auth_token_for_user(user)

            # Combine tokens
            tokens = {
                **jwt_tokens,
                **auth_token
            }

            # Check if this is an AJAX request or API request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json':
                other_users = User.objects.exclude(id=user.id)
                return JsonResponse({
                    'success': True,
                    'tokens': tokens,
                    'redirect_url': f'/chat/{other_users.first().username}/' if other_users.exists() else f'/chat/{user.username}/'
                })

            # Redirect to chat with another user or self
            other_users = User.objects.exclude(id=user.id)
            if other_users.exists():
                return redirect(f'/chat/{other_users.first().username}/')
            else:
                return redirect(f'/chat/{user.username}/')
        except Exception as e:
            messages.error(request, str(e))

            # Return JSON response for API requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)

    return render(request, 'register.html')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_auth_token(request):
    """Get or create an authentication token for the current user."""
    token_data = generate_auth_token_for_user(request.user)
    return Response(token_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_auth_jwt(request):
    """Generate JWT token for the authenticated user."""
    tokens = generate_tokens_for_user(request.user)
    return Response(tokens)

