FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /cryptoPoll
COPY requirements.txt /cryptoPoll/
RUN pip install -r requirements.txt
COPY . /cryptoPoll/