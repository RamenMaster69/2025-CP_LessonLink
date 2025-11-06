from rest_framework import serializers
from .models import Schedule
from .models import Exemplar


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ['id', 'user', 'subject', 'description', 'day', 'time']
        read_only_fields = ['user']  # Make user field read-only


class ExemplarSerializer(serializers.ModelSerializer):
    file_size_display = serializers.ReadOnlyField()
    upload_date_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Exemplar
        fields = [
            'id', 'name', 'file', 'file_type', 'file_size', 
            'file_size_display', 'extracted_text', 'upload_date',
            'upload_date_display'
        ]
        read_only_fields = ['file_type', 'file_size', 'extracted_text', 'upload_date']
    
    def get_upload_date_display(self, obj):
        return obj.upload_date.strftime('%b %d, %Y')