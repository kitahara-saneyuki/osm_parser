FROM apache/airflow:2.8.1
COPY requirements.txt /
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt

USER root
RUN apt-get update && apt-get install osm2pgsql -y
