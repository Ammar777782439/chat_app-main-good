from rest_framework import serializers
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for the Message model.

    This serializer handles the conversion between Message model instances and JSON representations.
    It includes validation for message content and defines which fields are read-only.

    Attributes:
        Meta: Contains metadata about the serializer, including the model, fields, and read-only fields.
    """

    class Meta:
        """
        Metadata for the MessageSerializer.

        Attributes:
            model: The model class this serializer is based on.
            fields: The fields to include in the serialized representation.
            read_only_fields: Fields that should not be modified during deserialization.
        """
        model = Message
        fields = ['id', 'sender', 'receiver', 'content', 'timestamp', 'deleted_at']
        read_only_fields = ['sender', 'timestamp', 'deleted_at']

    def validate_content(self, value):
        """
        Validate the content field of the message.

        This method ensures that the message content is not empty or just whitespace.

        Args:
            value (str): The content of the message to validate.

        Returns:
            str: The validated content if it passes validation.

        Raises:
            serializers.ValidationError: If the content is empty or contains only whitespace.
        """
        if not value.strip():
            raise serializers.ValidationError("Message content cannot be empty")
        return value