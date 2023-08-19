dc := docker compose

build:
	$(dc) build

init:
	$(dc) up airflow-init

up:
	$(dc) up -d

down:
	$(dc) down -v --remove-orphans --rmi all

test:
	$(dc) exec -T airflow-webserver airflow dags unpause 01_import_osm
	$(dc) exec -T airflow-webserver airflow dags unpause 03_parse_osm
	$(dc) exec -T airflow-webserver pytest -v --log-cli-level=INFO \
		--disable-warnings --cov-report term --cov=dags

shell:
	./airflow.sh bash

prune:
	docker system prune -a
