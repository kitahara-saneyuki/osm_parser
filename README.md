## OSM Routing Engine

Brief plan:
1. OSM Atlas (Airflow):
    1. Parse the road network into graph
    1. Easy to add plugin
1. OSM Routing API (Rust, Dijkstra / CCH):
    1. 1-1 routing
    1. 1-1 path
    1. matrix routing
    1. isochrone
    1. configurable
