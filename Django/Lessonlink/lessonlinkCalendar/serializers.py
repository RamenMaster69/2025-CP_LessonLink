from rest_framework import serializers
from .models import Event

class EventSerializer(serializers.ModelSerializer):
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'start_date', 'end_date',
            'location', 'venue', 'category', 'organizer', 'contact_info',
            'is_public', 'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

class EventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'start_date', 'end_date',
            'location', 'venue', 'category', 'organizer', 'contact_info', 'is_public'
        ]