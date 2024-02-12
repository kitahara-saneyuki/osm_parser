begin;
drop table if exists osm_modelingnodes;
create table osm_modelingnodes as
    select distinct on (osm_nodes.id)
        osm_nodes.id,
        cast(osm_nodes.lon as real) / 10000000 as longitude,
        cast(osm_nodes.lat as real) / 10000000 as latitude
    from osm_nodes inner join osm_roads
        on osm_nodes.id = ANY(osm_roads.nodes);

create index if not exists osm_modelingnodes_idx on osm_modelingnodes using btree(id);
create index if not exists osm_modelingnodes_longitude_idx on osm_modelingnodes using btree(longitude);
create index if not exists osm_modelingnodes_latitude_idx on osm_modelingnodes using btree(latitude);
commit;
