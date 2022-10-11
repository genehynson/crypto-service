FROM python:3-buster
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /crypto
COPY requirements.txt /crypto/
RUN apt-get update
RUN apt-get install cron -y
RUN touch /cron.log
RUN pip install -r requirements.txt
COPY . /crypto/