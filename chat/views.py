"""Views for the chat application.

This module contains the views and viewsets for the chat application, including:
- MessageViewSet: API endpoints for CRUD operations on messages
- chat_room: View for rendering the chat room interface

The views handle user authentication, message filtering, pagination, and WebSocket integration.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
import pytz
from rest_framework import serializers
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from chat.serializers import MessageSerializer
from .models import Message

# نمط التصميم facory
class MessagePagination(PageNumberPagination):
    """
    Custom pagination class for the Message API.

    This class configures how messages are paginated in API responses, allowing
    clients to request specific page sizes and limiting the maximum page size.

    Attributes:
        page_size (int): Default number of messages per page (10).
        page_size_query_param (str): Query parameter name for specifying page size ('page_size').
        max_page_size (int): Maximum allowed page size (100).
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


# نمط التصميم repository
class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling Message model CRUD operations through the API.

    This ViewSet provides endpoints for creating, retrieving, updating, and deleting messages,
    with additional custom actions for specific operations. It includes authentication,
    pagination, and filtering capabilities.

    Attributes:
        serializer_class: The serializer class used for message serialization/deserialization.
        permission_classes: List of permission classes that restrict access to authenticated users.
        pagination_class: The pagination class used for paginating message lists.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = MessagePagination
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        """
        Get the queryset of messages for the current user.

        This method filters messages to only include those where the current user
        is either the sender or receiver. It also supports filtering by another user
        when the 'user' query parameter is provided. Messages marked as deleted
        (deleted_at is not None) are excluded from the results.

        Returns:
            QuerySet: Filtered queryset of Message objects ordered by timestamp (newest first).
        """
        user = self.request.user
        other_user = self.request.query_params.get('user', None)

       
        queryset = Message.objects.filter(
            (Q(sender=user) | Q(receiver=user)),
            deleted_at__isnull=True  
        ).order_by('-timestamp')

      
        if other_user:
            queryset = queryset.filter(
                Q(sender__username=other_user) |
                Q(receiver__username=other_user)
            )

        return queryset

    def perform_create(self, serializer):
        """
        Perform the creation of a new message.

        This method is called when a new message is being created through the API.
        It sets the sender to the current user and finds the receiver based on the
        provided username.

        Args:
            serializer: The serializer instance that will create the message.

        Raises:
            ValidationError: If the specified receiver username doesn't exist.
        """
        receiver_username = self.request.data.get('receiver')

        try:
            receiver = User.objects.get(id=receiver_username)
            serializer.save(sender=self.request.user, receiver=receiver)
        except User.DoesNotExist:
            raise serializers.ValidationError("Receiver not found")

    @action(detail=True, methods=['delete'])
    def delete_message(self, request, pk=None):
        """
        Custom action to soft delete a message.

        This endpoint allows a user to delete their own message. It checks that the
        current user is the sender of the message before allowing deletion.
        Instead of permanently removing the message from the database, this method marks
        the message as deleted by setting its deleted_at field to the current timestamp.

        Args:
            request: The HTTP request object.
            pk: The primary key of the message to delete.

        Returns:
            Response: Empty response with 204 status code on success, or error response.
        """
        message = self.get_object()

       
        if message.sender != request.user:
            return Response({"error": "You can only delete your own messages"}, status=status.HTTP_403_FORBIDDEN)

      
        message.deleted_at = timezone.now()
        message.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def update_message(self, request, pk=None):
        """
        Custom action to update a message's content.

        This endpoint allows a user to edit the content of their own message. It checks that
        the current user is the sender of the message and that the new content is not empty.

        Args:
            request: The HTTP request object containing the new message content.
            pk: The primary key of the message to update.

        Returns:
            Response: Serialized message data on success, or error response.
        """
        message = self.get_object()

        
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
    """
    View function for rendering the chat room interface.

    This view displays the chat interface for conversations between the current user
    and another user specified by room_name. It retrieves and displays messages between
    the users, supports searching within messages, and provides a list of all users
    with their last messages for the sidebar.

    Args:
        request: The HTTP request object.
        room_name: The username of the other user in the conversation.

    Returns:
        HttpResponse: Rendered chat.html template with context data.
    """
    
    search_query = request.GET.get('search', '')

    
    users = User.objects.exclude(id=request.user.id)

    
    chats = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver__username=room_name)) |
        (Q(receiver=request.user) & Q(sender__username=room_name)),
        deleted_at__isnull=True  
    )
    # هانا تم اضافه الملاحظه ان لايتم حذف الرساله منقاعده البيانات

    
    if search_query:
        chats = chats.filter(Q(content__icontains=search_query))

   
    chats = chats.order_by('timestamp')

    
    user_last_messages = []

    
    min_datetime = timezone.now().replace(year=1, month=1, day=1)

   
    for user in users:
        last_message = Message.objects.filter(
            (Q(sender=request.user) & Q(receiver=user)) |
            (Q(receiver=request.user) & Q(sender=user)),
            deleted_at__isnull=True 
        ).order_by('-timestamp').first()

       
        user_last_messages.append({
            'user': user,
            'last_message': last_message,
            'timestamp': last_message.timestamp if last_message else min_datetime
        })

   
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





