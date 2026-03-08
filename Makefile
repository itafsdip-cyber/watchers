SHELL := /bin/bash

.PHONY: bootstrap up down logs ps app-up app-down

bootstrap:
	bash infra/scripts/bootstrap-mac.sh

up:
	docker compose up -d postgres redis

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

ps:
	docker compose ps

app-up:
	docker compose --profile app up -d

app-down:
	docker compose --profile app down
