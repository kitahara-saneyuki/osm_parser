#!/bin/bash
PGPASSFILE=$1 osm2pgsql -P 5432 --create $2 --verbose --database=$3 --user=$4 --host=$5 \
    --proj=4326 --latlong --prefix=osm --cache=4096 --slim --number-processes=8 --output=null
