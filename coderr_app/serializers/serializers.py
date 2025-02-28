from rest_framework import serializers
from ..models import FileUpload

class FileUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for file uploads.
    Handles file uploads and timestamps.
    """
    class Meta:
        model = FileUpload
        fields = ['file', 'uploaded_at']