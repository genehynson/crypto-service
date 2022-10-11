from django.forms import ValidationError
from django.http import HttpResponse
from django.http.response import JsonResponse
from rest_framework.decorators import api_view
from rest_framework import status
from django.core.validators import validate_slug
from . import query

@api_view(['GET'])
def index(request):
    if request.method == 'GET':
        return HttpResponse('Example request: GET /btcusd?duration=-24h&exchange=kraken', status=status.HTTP_200_OK)
        
@api_view(['GET'])
def crypto_metric(request, pair):
    if request.method == 'GET':
        duration = request.GET.get('duration', '-24h')
        exchange = request.GET.get('exchange', None)
        try:
            validate_slug(duration)
            if exchange != None:
                validate_slug(exchange)
        except ValidationError:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)
        price_query_results = query.query_price_metric(pair, exchange, duration)
        rank_query_results = query.query_stddev_price_metric(pair, exchange, duration)
        response = {'pair': pair, 'rank': rank_query_results, 'duration': duration, 'prices': price_query_results}
        return JsonResponse(response, status=status.HTTP_200_OK)
