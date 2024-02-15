begin;
drop table if exists osm_routingnodes;
CREATE TABLE osm_routingnodes_temp (
    id serial,
    osm_id bigint unique
);

INSERT INTO osm_routingnodes_temp(osm_id)
    select distinct start_node from osm_roads
    ON CONFLICT do nothing;
INSERT INTO osm_routingnodes_temp(osm_id)
    select distinct end_node from osm_roads
    ON CONFLICT do nothing;

create table if not exists osm_crossings as
    select distinct unnest(nodes) as unnested_nodes, array_agg(distinct id) as osm_ids from osm_roads
    group by unnested_nodes
    having array_length(array_agg(distinct id), 1) > 1;

INSERT INTO osm_routingnodes_temp(osm_id)
    select unnested_nodes from osm_crossings
    ON CONFLICT do nothing;
drop table if exists osm_crossings;

create table osm_routingnodes as
    select ort.osm_id as osm_id, point(om.longitude, om.latitude) as coord, om.longitude, om.latitude
        from osm_routingnodes_temp ort inner join osm_modelingnodes om on ort.osm_id = om.id;
ALTER TABLE osm_routingnodes ADD COLUMN id SERIAL PRIMARY KEY;

drop table if exists osm_routingnodes_temp;

create index osm_routingnodes_osm_idx on osm_routingnodes using btree(osm_id);
create index osm_routingnodes_coord_idx on osm_routingnodes using gist(coord);
commit;
