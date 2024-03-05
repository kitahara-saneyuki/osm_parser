-- Step 2.1: all the roads
begin;
drop table if exists osm_highways_temp;
create table osm_highways_temp as
    select id, nodes, hstore(
        string_to_array(regexp_replace(array_to_string(tags, '@*#&'), $$['",{}]$$, '`'), '@*#&')) as temp_tags
    from osm_ways where 'highway'=ANY(tags);

drop table if exists osm_highways;
create table osm_highways as
    select id, nodes,
           delete(temp_tags, array['highway', 'access', 'oneway', 'name']) as tags,
           temp_tags -> 'highway' as highway,
           temp_tags -> 'access' as access,
           temp_tags -> 'oneway' as oneway,
           temp_tags -> 'name' as name,
           temp_tags -> 'maxspeed' as maxspeed_str
    from osm_highways_temp;

drop table if exists osm_highways_temp;
commit;

begin;
alter table osm_highways add column maxspeed int;
-- assume the unit of maxspeed is mph -- most of our use case is in US
update osm_highways set maxspeed = cast(maxspeed_str as smallint) WHERE maxspeed_str ~ E'^\\d+$';
-- convert the mph maxspeed
update osm_highways set maxspeed = cast(rtrim(maxspeed_str, ' mph') as smallint) WHERE rtrim(maxspeed_str, ' mph') ~ E'^\\d+$';
update osm_highways set maxspeed = null where not (maxspeed_str ~ E'^\\d+$' or rtrim(maxspeed_str, ' mph') ~ E'^\\d+$');
alter table osm_highways drop column maxspeed_str;
commit;
