#!/bin/bash
sed -i 's/\\\}/,}/g' $2/edges.csv
sed -i 's/,,/,0,/g' $2/edges.csv
sed -i 's/,}/}/g' $2/edges.csv
sed -i 's/,,/,0,/g' $2/edges.csv

PGPASSFILE=$1 psql -p 5432 -h $3 -U $4 -d $5 -c "\copy \
    osm_edges_temp (edge_nodes, way_startoffset, way_endoffset, way_len, start_node, end_node, osm_wayid) \
    from '$2/edges.csv' with csv delimiter E'\x02' quote E'\x03';"
