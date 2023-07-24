dc := docker compose

init:
	$(dc) up airflow-init

up:
	$(dc) up -d

down:
	$(dc) down -v --remove-orphans --rmi all

shell:
	./airflow.sh bash

prune:
	docker system prune -a
