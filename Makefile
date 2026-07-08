.PHONY: build up down clean

build:
	docker build -t my-server-image ./server
	docker compose build

up: build
	docker compose up -d

down:
	docker compose down
	-docker stop $$(docker ps -a -q --filter name=server_) 2>/dev/null || true
	-docker rm $$(docker ps -a -q --filter name=server_) 2>/dev/null || true

clean: down
	docker system prune -f

test:
	python3 analysis.py
