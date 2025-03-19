from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse

from chat.serializers import MessageSerializer
from .models import Message
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
import pytz
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Q

class MessagePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = MessagePagination

    def get_queryset(self):
        user = self.request.user
        other_user = self.request.query_params.get('user', None)

        queryset = Message.objects.filter(
            (Q(sender=user) | Q(receiver=user))
        ).order_by('-timestamp')

        if other_user:
            queryset = queryset.filter(
                Q(sender__username=other_user) |
                Q(receiver__username=other_user)
            )

        return queryset

    def perform_create(self, serializer):
        receiver_username = self.request.data.get('receiver')
        try:
            receiver = User.objects.get(username=receiver_username)
            serializer.save(sender=self.request.user, receiver=receiver)
        except User.DoesNotExist:
            from rest_framework import serializers
            raise serializers.ValidationError("Receiver not found")

    @action(detail=True, methods=['delete'])
    def delete_message(self, request, pk=None):
        message = self.get_object()

        # Check if the user is the sender of the message
        if message.sender != request.user:
            return Response({"error": "You can only delete your own messages"}, status=status.HTTP_403_FORBIDDEN)

        message.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def update_message(self, request, pk=None):
        message = self.get_object()

        # Check if the user is the sender of the message
        if message.sender != request.user:
            return Response({"error": "You can only edit your own messages"}, status=status.HTTP_403_FORBIDDEN)

        content = request.data.get('content')
        if not content or not content.strip():
            return Response({"error": "Message content cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        message.content = content
        message.save()

        serializer = self.get_serializer(message)
        return Response(serializer.data)



@login_required
def chat_room(request, room_name):
    search_query = request.GET.get('search', '')
    users = User.objects.exclude(id=request.user.id)
    chats = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver__username=room_name)) |
        (Q(receiver=request.user) & Q(sender__username=room_name))
    )

    if search_query:
        chats = chats.filter(Q(content__icontains=search_query))

    chats = chats.order_by('timestamp')
    user_last_messages = []

    # Use timezone.now() for the minimum datetime
    min_datetime = timezone.now().replace(year=1, month=1, day=1)

    for user in users:
        last_message = Message.objects.filter(
            (Q(sender=request.user) & Q(receiver=user)) |
            (Q(receiver=request.user) & Q(sender=user))
        ).order_by('-timestamp').first()

        user_last_messages.append({
            'user': user,
            'last_message': last_message,
            'timestamp': last_message.timestamp if last_message else min_datetime
        })

    # Sort using the timestamp key
    user_last_messages = sorted(
        user_last_messages,
        key=lambda x: x['timestamp'],
        reverse=True
    )

    return render(request, 'chat.html', {
        'room_name': room_name,
        'chats': chats,
        'users': users,
        'user_last_messages': user_last_messages,
        'search_query': search_query,
        'slug': room_name  # Add slug variable for WebSocket connection
    })





