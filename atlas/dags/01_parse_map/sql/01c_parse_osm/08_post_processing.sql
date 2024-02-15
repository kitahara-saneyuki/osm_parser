-- Step 3: post processing of edges
begin;

create index osm_edges_temp_osm_idx on osm_edges_temp using btree(osm_wayid);
delete from osm_edges_temp where start_node = end_node;
create table osm_edges_temp1 as
    select oet.*, or2.tags, or2.highway, or2.oneway, or2.maxspeed, or2.nodes as osm_waynodes from osm_edges_temp oet
        inner join osm_roads or2 on oet.osm_wayid = or2.id;
drop table if exists osm_edges_temp;

create index osm_edges_temp1_start_idx on osm_edges_temp1 using btree(start_node);

create table osm_edges_temp2 as
    select oet1.*, orn.id as start_node_id from osm_edges_temp1 oet1 inner join osm_routingnodes orn
        on oet1.start_node = orn.osm_id;
drop table if exists osm_edges_temp1;
create index osm_edges_temp2_end_idx on osm_edges_temp2 using btree(end_node);

create table osm_edges as
    select oet2.*, orn.id as end_node_id from osm_edges_temp2 oet2 inner join osm_routingnodes orn
        on oet2.end_node = orn.osm_id;
drop table if exists osm_edges_temp2;

create index if not exists osm_edges_osm_idx on osm_edges using btree(osm_wayid);
create index if not exists osm_edges_edge_nodes_idx on osm_edges using gin(edge_nodes);
create index if not exists osm_edges_start_node_idx on osm_edges using btree(start_node);
create index if not exists osm_edges_end_node_idx on osm_edges using btree(end_node);
create index if not exists osm_edges_start_idx on osm_edges using btree(start_node_id);
create index if not exists osm_edges_end_idx on osm_edges using btree(end_node_id);
create index if not exists osm_edges_oneway_idx on osm_edges using btree(oneway);

commit;
