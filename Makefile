dc := docker compose

up:
	$(dc) up -d

down:
	$(dc) down -v --remove-orphans --rmi all

shell:
	./airflow.sh bash

prune:
	docker system prune -a
