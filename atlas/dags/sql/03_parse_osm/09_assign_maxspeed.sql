update osm_edges set maxspeed = 65
where highway = 'motorway'
and maxspeed is null;

update osm_edges set maxspeed = 55
where (highway = 'trunk' 
or highway = 'primary')
and maxspeed is null;

update osm_edges set maxspeed = 40
where (highway = 'motorway_link'
or highway = 'trunk_link'
or highway = 'primary_link'
or highway = 'secondary')
and maxspeed is null;

update osm_edges set maxspeed = 30
where (highway = 'secondary_link'
or highway = 'tertiary'
or highway = 'tertiary_link')
and maxspeed is null;

update osm_edges set maxspeed = 20
where (highway = 'residential'
or highway = 'unclassified'
or highway = 'road')
and maxspeed is null;

update osm_edges set maxspeed = 15
where highway = 'living_street'
and maxspeed is null;

update osm_edges set time_cost = (way_endoffset - way_startoffset) * 1000 / (cast (maxspeed as real) * 0.44704);
-- meter / (mile / hr) = meter / (1609.34 meter / 3600 sec) = sec / 0.44704
-- so the unit of time_cost is second, we can multiply it by 1000 to have millisecond

update osm_edges
set oneway = 'yes'
where oneway = '1' or oneway = 'alternating' or oneway = 'reversible';
