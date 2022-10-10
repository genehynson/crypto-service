from rest_framework import serializers 
from service.models import Poll
 
 
class PollSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = Poll
        fields = ('url',
                  'interval_ms')