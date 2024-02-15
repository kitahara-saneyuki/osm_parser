CREATE EXTENSION if not exists postgis;
CREATE EXTENSION if not exists hstore;
create extension if not exists cube;
create extension if not exists earthdistance;

drop table if exists osm_nodes;
drop table if exists osm_rels;
drop table if exists osm_ways;
