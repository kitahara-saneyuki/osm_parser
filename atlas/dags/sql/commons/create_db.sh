#!/bin/bash
PGPASSFILE=$1 psql -h $6 -U $7 $8 -c "create user $3 superuser;\
    alter user $3 with encrypted password '$4';" || true
PGPASSFILE=$1 psql -h $6 -U $7 $8 -c "CREATE DATABASE $5 OWNER $3;" || true
PGPASSFILE=$2 psql -h $6 -U $3 $5 -f dags/sql/commons/drop_osm_tables.sql
