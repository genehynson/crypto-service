# Crypto Price Service

## Overview

This Python service queries `https://api.cryptowat.ch`'s public API endpoints to retrieve the latest pricing information for each Crypto pair across all markets. This data is stored in InfluxDB and can be queried using the API endpoint provided by this service.

## How it works

The service uses Django to host a web server that responds to incoming REST HTTP requests. The Django server also runs an app called crontab which schedules a cron task to be run using the native Linux OS cron service.

The cron task executes once per minute and makes a REST API request to the url `https://api.cryptowat.ch/markets/prices`. This endpoint returns the latest price of each Crypto from each market available on the cryptowat platform. The price data is then converted into Line Protocol so it can be consumed by InfluxDB.

InfluxDB is a natural choice for a backend to this problem since the price data we're persisting is timeseries data. Overtime we're going to collect a _lot_ of data and InfluxDB is able to store this data more effectively than SQL DBs, such as Postgres.

When the user makes a HTTP request to our hosted endpoints, this service makes two queries to InfluxDB: 1) get the price data for the requested crypto pair and 2) calculate the rank of the reuqested crypto pair. The results are formatted in a user-friendly json object and returned to the user.

## Source code layout

Most of the files are generated from Django's starter project. Here are some others of interest:

- `crypto/crypto/cron.py`: Contains the function `crypto_price_cron()` that is run on a cron schedule.
- `crypto/crypto/settings./py`: Contains the cron job settings at the bottom of the file.
- `crypto/crypto/service/query.py`: Contains the InfluxDB queries to list price data and compute the rank metric.
- `crypto/crypto/service/views.py`: Contains the API endpoint definitions.
- `docker-compose.yml`: Contains the environment configuration for the Django app and InfluxDB.

## How to get it running

To make things simple I've containerized the crypto service and provided a `docker-compose.yml` file to run the crypto service alongside InfluxDB. The docker compose file contains all the environment variables neccesary for the crypto service to successfully communicate with InfluxDB.

I've also included a `Makefile` with some common commands.

After cloning this repo, simply run the following commands to get the service running:
- `make build`
- `make start`

Once the service is running, the API can be accessed at `localhost:8001`.

InfluxDB can be accessed at `localhost:8086`.

## Example API usage

The API endpoint takes the crypto pair as a route parameter and has two optional query parameters:
1. exchange - filters results to a specific exchange/market (default: `None`)
2. duration - specifies the query duration start (default: `-24h`)

Request: `GET localhost:8001/btcusd`

Response (partial):

```json
{
  "pair": "btcusd",
  "rank": "28/13827",
  "duration": "-24h",
  "prices": [
    {
      "price": 19062.76,
      "time": "2022-10-11T01:20:02.951Z",
      "exchange": "binance-us"
    },
    {
      "price": 19058.62,
      "time": "2022-10-11T01:21:02.259Z",
      "exchange": "binance-us"
    },
    {
      "price": 19058.62,
      "time": "2022-10-11T01:22:02.471Z",
      "exchange": "binance-us"
    },
    {
      "price": 19064.75,
      "time": "2022-10-11T01:23:02.595Z",
      "exchange": "binance-us"
    },
    {
      "price": 19058.57,
      "time": "2022-10-11T01:24:02.716Z",
      "exchange": "binance-us"
    },
...
```

Request: `GET localhost:8001/btcusd?duration=-1h&exchange=bisq`

Response (partial):

```json
{
  "pair": "btcusd",
  "rank": "4/9",
  "duration": "-1h",
  "prices": [
    {
      "price": 20966.789,
      "time": "2022-10-11T03:35:02.358Z",
      "exchange": "bisq"
    },
    {
      "price": 20966.789,
      "time": "2022-10-11T03:36:02.473Z",
      "exchange": "bisq"
    },
    {
      "price": 20966.789,
      "time": "2022-10-11T03:37:02.904Z",
      "exchange": "bisq"
    },
    {
      "price": 20966.789,
      "time": "2022-10-11T03:39:03.718Z",
      "exchange": "bisq"
    },
...
```

## Improvements and considerations

Considering this project was built in an afternoon, there are some limitations. Let's discuss some potential improvements to this project that would make it closer to production-ready.

### Parallel processing

Right now the two queries to InfluxDB are syncronous and can take some time to complete. One obvious improvement would be to execute the two queries in parallel as this would improve the API response time. 

### Streaming the response

Another major improvement to API response time would be to use Django's `StreamingHTTPResponse` to stream the query response to the user as we recieve it. Instead of collecting the entire response in memory from InfluxDB, transforming it to another object in memory, and then finally releasing it we could simply stream the response and transform it line by line. InfluxDB supports this streaming capability. This would also help reduce memory consumption of this crypto service.

### Pre-calculate the rank metric

Right now this crypto service calculates the rank of the requested crypto pair on demand. This is a very expensive query for InfluxDB because it requires computing the stddev of every crypto pair over the last 24 hours. Since we only update the price of each crypto pair each minute, it seems reasonable that we could pre-calculate the rank metric of each crypto pair. This could be accomplished with another cron task or using an InfluxDB "Task" (which is essentially a Flux script run on a schedule). The output of this task would be a new measurement in the InfluxDB bucket that tracks the latest rank of each metric. This improvement would improve the API response significantly. The downside being that our service is performing work even when the information is not needed.

## Scalability

There are 3 components to this solution that would be scaled individually:
1. Web server
2. Cron job
3. InfluxDB

The web server is stateless (besides the Django starter project admin stuff) and can be scaled vertically and horizontally to match user demand and/or if additional API endpoints are desired.

The cron job currently takes ~0.5 seconds to query the latest price data and write it to InfluxDB. This delay isn't noticable with a run interval of 1 minute. But if we were to try and increase that interval to 1 second, then this delay would become problematic. The cron job would need to be refactored to utilize parallel processing to improve its processing time. Instead of querying the `/markets/prices` endpoint to get all the data in one-shot we would break this down into a multi-step process:

1. Get the market + crypto pair identifiers using `/markets` endpoint (this data could be cached)
2. Query latest price of each identifier individually using `/markets/:exchange/:pair/price` endpoint.
3. Write data to InfluxDB in batches (InfluxDB is most efficient with batch writes)

This multi-step process would allow us to split step 2 into many threads. We could scale the number of threads up or down depending on demand and resources available. And to achieve even greater results, the threads could be converted into a separate containerized service that is scaled horizontally and assigned the sole task of querying the `/markets/:exchange/:pair/price` endpoint for specific exchange/pair combo(s).

The InfluxDB backend can be scaled vertically to meet the demands of this service...to a point. Unfortunately, InfluxDB OSS doesn't offer great support for horizontal replication through clustering. Scalability comes at a price through InfluxData's InfluxDB Cloud PAYG offering. But since InfluxDB will be the bottleneck of our service, it is likely worth the cost.

That being said, an alternative solution to horizontal replication through clustering with InfluxDB would be sharding. The cryto pairs could be divided into buckets and assigned an InfluxDB instance. The cron tasks would write the metrics to the appropriate InfluxDB instance. And the web server would query all the InfluxDB instances to produce the complete results. Even though multiple queries would need to be executed, the overall result would be faster because each InfluxDB instance would contain less data. The downside to this solution is that our 'rank' calculation would have to be computed in the web server after all the results were retrieved, potentially slowing the API response time.

Overall these scalability improvements could help this service achieve faster API response times, handle higher demand, and support capturing additional crypto metrics.

## Testing

A multi-component service such as this one should test each component individually and together. 
- Unit tests for the business logic in the API endpoints and cron job should be added. 
- Functional tests of the API endpoints should be added to verify it response with the appropriate status codes and error messages during edge cases. These tests should use mock responses from InfluxDB.
- Functional tests of the cron job should be added to verify it handles unexpected responses from cryptowat. These tsts should use mock responses from the `/markets/prices` endpoint.
- End-to-end tests should be created to test the "happy paths" of the entire service. These tests should use live data.


## Feature request

>  to help the user identify opportunities in real-time, the app will send an alert whenever a metric exceeds 3x the value of its average in the last 1 hour. For example, if the volume of GOLD/BTC averaged 100 in the last hour, the app would send an alert in case a new volume data point exceeds 300.

This feature request could be completed by introducing a new cron job or by using InfluxDB's Alert capability. Either way a Flux query would be executed on an interval and would calcuate the average of each crypto pair over the last hour. This average would be compared to the latest price value and if the latest price is 3x the computed average, a notification would be sent.

This new cron job could be scaled horizontally in a similar fashion to the methods described above (i.e. divide and conquor).

The user could sign up for alerts by making a POST request to `localhost:8001/alerts` and include a webhook URL or email address in the body of the request. Our web server would store this information in a relational DB. When a 3x opportunity is identified by the new cron job, a single, async, POST request would be made to from the cron job to our web server. The web server would respond by querying the relational DB and invoking the webhook URL or email of each record. 



