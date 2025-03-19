from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'messages', views.MessageViewSet, basename='message')

urlpatterns = [
    path('api/', include(router.urls)),
    path('chat/<str:room_name>/', views.chat_room, name='chat'),
]
