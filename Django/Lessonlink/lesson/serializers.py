from rest_framework import serializers
from .models import Schedule

class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ['id', 'user', 'subject', 'description', 'day', 'time']
        read_only_fields = ['user']  # Make user field read-only