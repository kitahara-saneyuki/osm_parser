begin;
drop table if exists osm_edges;
drop table if exists osm_edges_temp;
CREATE TABLE osm_edges_temp (
    id serial,
    edge_nodes bigint[],
    way_startoffset real,
    way_endoffset real,
    way_len real,
    time_cost real,
    start_node bigint,
    end_node bigint,
    osm_wayid bigint
);
commit;
