start:
	docker-compose up
stop:
	docker-compose down
build:
	docker-compose build
freeze:
	cd crypto && pip3 freeze > requirements.txt
all: | freeze build start
exec:
	docker exec -it crypto-service_crypto-service_1 bash