from influxdb_client import InfluxDBClient
from django.conf import settings

client = InfluxDBClient(url=settings.INFLUXDB_ADDRESS, token=settings.INFLUXDB_TOKEN, org=settings.INFLUXDB_ORG)
query_api = client.query_api()

def query_price_metric(pair, exchange=None, duration='-24h'):
    # this query returns the prices of a crypto pair over a duration.
    query = f'from(bucket:"{settings.INFLUXDB_BUCKET}")\
    |> range(start: {duration})\
    |> filter(fn:(r) => r._measurement == "crypto_prices")\
    |> filter(fn: (r) => r["pair"] == "{pair}")'
    if exchange != None:
        query += f'|> filter(fn: (r) => r["exchange"] == "{exchange}")'
    query += '|> filter(fn:(r) => r._field == "price")'
    result = query_api.query(org=settings.INFLUXDB_ORG, query=query)
    return format_influxdb_price_result(result)

def format_influxdb_price_result(result):
    # format the price results from influxdb into a new dictionary
    formatted_results = []
    for table in result:
        for record in table.records:
            formatted_results.append({'price': record.get_value(), 'time': record.get_time(), 
            'exchange': record.values.get('exchange')})
    return formatted_results

def query_stddev_price_metric(pair, exchange=None, duration='-24h'):
    # this query returns the stddev of the price of each market+pair
    # sorted from largest to smallest over a duration.
    query = f'from(bucket:"{settings.INFLUXDB_BUCKET}")\
    |> range(start: {duration})\
    |> filter(fn: (r) => r["_measurement"] == "crypto_prices")\
    |> filter(fn: (r) => r["_field"] == "price")'
    if exchange != None:
        query += f'|> filter(fn: (r) => r["exchange"] == "{exchange}")'
    query += '|> stddev()\
    |> group()\
    |> sort(desc: true)'
    result = query_api.query(org=settings.INFLUXDB_ORG, query=query)
    return find_rank_of_pair(pair, result)

def find_rank_of_pair(pair, result):
    # find the 'rank' of this pair by finding the index of its first
    # appearance in the sorted array of price stddevs.
    for table in result:
        for i, record in enumerate(table.records):
            if (record.values.get('pair') == pair):
                return f'{i+1}/{len(table.records)}'
    return -1
