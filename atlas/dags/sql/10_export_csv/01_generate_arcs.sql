begin;
update osm_edges
set time_cost = (way_endoffset - way_startoffset) * 1000 / (cast (maxspeed as real) * 0.44704)
where maxspeed > 0;
update osm_edges
set time_cost = 2147483647
where maxspeed = 0;
-- meter / (mile / hr) = meter / (1609.34 meter / 3600 sec) = sec / 0.44704
-- so the unit of time_cost is second, we can multiply it by 1000 to have millisecond

update osm_edges
set oneway = 'yes'
where oneway = '1' or oneway = 'alternating' or oneway = 'reversible';
commit;

begin;
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
commit;
