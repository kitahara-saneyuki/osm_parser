dc := docker compose

build:
	$(dc) build

init:
	$(dc) up airflow-init

up:
	$(dc) up -d

down:
	$(dc) down -v --remove-orphans --rmi all

unpause:
	$(dc) exec -T airflow-webserver airflow dags unpause 01a_download_pbf
	$(dc) exec -T airflow-webserver airflow dags unpause 01a_set_test_vars
	$(dc) exec -T airflow-webserver airflow dags unpause 01b_import_osm
	$(dc) exec -T airflow-webserver airflow dags unpause 01c_parse_osm
	$(dc) exec -T airflow-webserver airflow dags unpause 01d_assign_maxspeed
	$(dc) exec -T airflow-webserver airflow dags unpause 10_export_csv

test:
	$(dc) exec -T airflow-webserver pytest -v --log-cli-level=INFO \
		--disable-warnings --cov-report term --cov=dags

run:
	$(dc) exec -T airflow-webserver airflow dags trigger $(step) \
		-o yaml -c '{"atlas_region": "$(region)"}'

shell:
	./airflow.sh bash

prune:
	docker system prune -a
