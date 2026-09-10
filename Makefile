COMPOSE ?= docker compose

.PHONY: help up up-d down clean logs ps build test test-java test-python seed

help:
	@echo "Планирование спринтов — команды:"
	@echo "  make up          - собрать и запустить весь стек (db + java + python + web) на :8080"
	@echo "  make up-d        - то же в фоне"
	@echo "  make down        - остановить контейнеры"
	@echo "  make clean       - остановить и удалить тома (сбросить БД)"
	@echo "  make logs        - логи всех сервисов"
	@echo "  make ps          - статус контейнеров"
	@echo "  make build       - собрать образы без запуска"
	@echo "  make test        - тесты Java (Spring Boot + H2) и Python"
	@echo "  make test-java   - только Java-тесты"
	@echo "  make test-python - только Python-тесты"
	@echo "  make seed        - перегенерировать Flyway-миграцию из data/seed.json"

up:
	$(COMPOSE) up --build

up-d:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

clean:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

build:
	$(COMPOSE) build

test-java:
	cd backend-java && mvn -B -ntp test

test-python:
	python analytics-python/tests/test_compute.py

test: test-java test-python

seed:
	python scripts/gen_initsql.py
