FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /cryptoApi
COPY requirements.txt /cryptoApi/
RUN pip install -r requirements.txt
COPY . /cryptoApi/