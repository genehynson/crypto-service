from django.conf import settings
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from time import time
import requests

client = InfluxDBClient(url=settings.INFLUXDB_ADDRESS, token=settings.INFLUXDB_TOKEN, org=settings.INFLUXDB_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

def crypto_price_cron():
    print('Fetching latest crypto prices across all markets and pairs...')
    begin = time()

    prices = get_latest_crypto_prices()
    line_protocol = convert_results_to_lineprotocol(prices)
    write_lp_to_influxdb(line_protocol)

    end = time()
    print(f'All {len(prices)} price metrics written to InfluxDB in {end - begin} seconds')

def get_latest_crypto_prices():
    # fetches the latest crypto prices across all markets.
    resp = requests.get(f'{settings.CRYPTOWAT_BASE_API_URL}/markets/prices')
    data = resp.json()
    return data['result']
    
def convert_results_to_lineprotocol(result):
    # converts the prices into Line Protocol
    all_line_protocol = []
    for key in result:
        # key example: 'market:binance-us:atomusd'
        parts = key.split(':')
        if (len(parts) != 3):
            print(f'Unexpected key format, skipping: {key}')
            continue
        exchange_type = parts[0]
        exchange = parts[1]
        pair = parts[2]
        price = result[key]
        lp = f'crypto_prices,type={exchange_type},exchange={exchange},pair={pair} price={price}'
        all_line_protocol.append(lp)
    return all_line_protocol

def write_lp_to_influxdb(line_protocol):
    # writes the LP price data to InfluxDB
    write_api.write(settings.INFLUXDB_BUCKET, settings.INFLUXDB_ORG, line_protocol)
