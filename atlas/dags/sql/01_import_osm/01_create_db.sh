#!/bin/bash
# ignore errors if DB already exists
PGPASSFILE=$1 psql -h $6 -U $7 $8 -c "create user $3 superuser;\
    alter user $3 with encrypted password '$4';" || true
PGPASSFILE=$1 psql -h $6 -U $7 $8 -c "CREATE DATABASE $5 OWNER $3;" || true

# for idempotence, drop all the tables created by osm2pgsql
PGPASSFILE=$2 psql -h $6 -U $3 $5 -f dags/sql/01_import_osm/02_drop_osm_tables.sql

mkdir -p data/$9/osm data/$9/temp data/$9/output || true
