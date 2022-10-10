from asyncore import poll
from django.shortcuts import render
from django.http import HttpResponse
from service.models import Poll
from django.core import serializers
from service.serializers import PollSerializer
from rest_framework.parsers import JSONParser
from django.http.response import JsonResponse
from rest_framework.decorators import api_view
from rest_framework import status

@api_view(['GET', 'POST'])
def index(request):
    if request.method == 'GET':
        return HttpResponse(serializers.serialize("json", Poll.objects.all()))
    elif request.method == 'POST':
        poll_data = JSONParser().parse(request)
        poll_serializer = PollSerializer(data=poll_data)
        if poll_serializer.is_valid():
            poll_serializer.save()
            return JsonResponse(poll_serializer.data, status=status.HTTP_201_CREATED) 
        return JsonResponse(poll_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['DELETE'])
def poll(request, pk):
    try: 
        poll = Poll.objects.get(pk=pk) 
    except Poll.DoesNotExist: 
        return HttpResponse(status=status.HTTP_404_NOT_FOUND) 
    if request.method == 'DELETE':
        poll.delete()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)
