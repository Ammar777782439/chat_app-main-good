
from django.urls import path
from django.contrib.auth.views import LogoutView
from users.views import login_view, register_view, home_view, get_auth_token, obtain_auth_token

urlpatterns = [
    path('', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', LogoutView.as_view(
        next_page='login',
        template_name='login.html'
    ), name='logout'),

    # API endpoints
    path('api/token/', get_auth_token, name='get_auth_token'),
    path('api/auth/login/', obtain_auth_token, name='api_token_auth'),
]
