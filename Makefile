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
	$(dc) exec -T airflow-webserver airflow dags unpause 01_import_osm
	$(dc) exec -T airflow-webserver airflow dags unpause 03_parse_osm
	$(dc) exec -T airflow-webserver airflow dags unpause 05_export_osm

test:
	$(dc) exec -T airflow-webserver pytest -v --log-cli-level=INFO \
		--disable-warnings --cov-report term --cov=dags

run:
	$(dc) exec -T airflow-webserver airflow dags trigger 01_import_osm \
		-o yaml -c '{"atlas_region": "$(region)"}'

shell:
	./airflow.sh bash

prune:
	docker system prune -a

python37:
	sudo apt-get update && sudo apt-get upgrade
	sudo apt-get install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libsqlite3-dev \
		libreadline-dev libffi-dev curl libbz2-dev wget default-libmysqlclient-dev python3-dev libxml2-dev libxslt1-dev \
		libsasl2-dev libldap2-dev libjpeg-dev libpq-dev liblcms2-dev libblas-dev libatlas-base-dev -y
	sudo mkdir -p /usr/local/share/python3.7
	wget -qO- https://www.python.org/ftp/python/3.7.16/Python-3.7.16.tar.xz | \
		sudo tar -xJ -C /usr/local/share/python3.7 \--strip-components 1
	cd /usr/local/share/python3.7 \
		&& sudo bash configure --enable-optimizations --enable-shared \
		&& sudo make -j8 build_all \
		&& sudo make -j8 altinstall \
		&& sudo ldconfig /usr/local/share/python3.7
	curl -sS https://bootstrap.pypa.io/get-pip.py | python3
	pip3.7 install virtualenv
