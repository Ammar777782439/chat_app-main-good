
from django.urls import path
from django.contrib.auth.views import LogoutView
from users.views import login_page, logout_page, signup_view,login_view,register_view

urlpatterns = [
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
     path('logout/', LogoutView.as_view(
        next_page='login',
        template_name='login.html'
    ), name='logout'),

    # path('', login_page, name="login"),
    # path('logout/', logout_page, name="logout"),
    # path('signup/', signup_view, name="signup"),
]
