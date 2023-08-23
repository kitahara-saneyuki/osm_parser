drop table if exists osm_arcs;
CREATE TABLE osm_arcs (
    id serial,
    start_node_id bigint,
    end_node_id bigint,
    time_cost real
);

-- TODO: change to update
insert into osm_arcs (start_node_id, end_node_id, time_cost)
select edges.start_node_id, edges.end_node_id, edges.time_cost from osm_edges edges
where oneway is null or oneway = 'no' or oneway = 'yes';

insert into osm_arcs (start_node_id, end_node_id, time_cost)
select edges.end_node_id, edges.start_node_id, edges.time_cost from osm_edges edges
where oneway is null or oneway = 'no' or oneway = '-1';
