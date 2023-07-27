FROM apache/airflow:2.6.3
COPY requirements.txt /
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt

USER root
RUN apt-get update && apt-get upgrade -y && \
    apt-get install rename libgdal-dev osm2pgsql -y

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
