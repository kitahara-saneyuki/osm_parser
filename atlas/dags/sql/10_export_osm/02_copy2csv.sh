#!/bin/bash
PGPASSFILE=$1 psql -h $3 -U $4 -d $5 -c "\copy \
    (select coord[1] as lat, coord[0] as lon from osm_routingnodes order by id) \
    to '$2/node_$5.csv' delimiter ',' CSV HEADER;"
PGPASSFILE=$1 psql -h $3 -U $4 -d $5 -c "\copy \
    (select (start_node_id - 1) as head, (end_node_id - 1) as tail, (cast(time_cost as integer)) as weight from osm_arcs
    where start_node_id is not null and end_node_id is not null and time_cost is not null
    order by id) \
    to '$2/graph_$5.csv' delimiter ',' CSV HEADER"
mkdir -p $2/$5/
PGPASSFILE=$1 psql -h $3 -U $4 -d $5 -c "\copy \
    (select max(id) from osm_routingnodes) \
    to '$2/$5/max_road_id.csv' delimiter ',' CSV HEADER;"
