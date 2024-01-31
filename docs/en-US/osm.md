# OpenStreetMap Parsing

[中文](./docs/zh-CN/osm-zh-CN.md) | English

OpenStreetMap (hereafter OSM)[^1] uses a data structure, the so-called `way` [^2] to store road traffic networks.
What we are concerned:

1. is the OSM road traffic map a mathematical Graph[^3]?
1. how can we understand and analyze the XML data of OSM?
1. the basic attributes of each road section [^4], such as
    1. road length
    1. travel speed, generally determined by the `highway` [^5].
    1. road direction

We will look into those questions.

## Transportation network as a mathematical graph

Since this is not about routing algorithms (e.g., dijkstra), we can skip the discussion of the data structure representation of graphs.

Transportation network, as the necessity of weights and oneways (like almost all the freeway and overpass ramps), are represented as a **weighted directed graph**.

A weighted directed graph $G = (V, E)$ contains two main elements, namely
- Nodes ($V$, vertices), intersections of roads.
- Edges ($E$, also labeled as arcs $A$), i.e., roads.

Each road segment has its own weight, depending on the requirements:
- speed
- time cost of travel
- Length (distance)

In a weighted directed graph, nodes pointing to their own rings (e.g., a ring of roads ending in a residential area) have less significance in routing and may cause undefined behavior of the routing algorithm.
Therefore we omit them and use Directed Acyclic Graph (DAG) in routing.

## osm2pgsql

We use osm2pgsql to parse the OSM data into a PostgreSQL database.
This is a tedious process, so we skip the discussion and refer to the osm2pgsql documentation[^6] for those interested.

We download the packaged `.osm.pbf` map file from Geofabrik[^7].
Running osm2pgsql to parse OSM into PostgreSQL as raw data. What we cared about are the ways, as all the roads (highways) are served as ways.



[^1]: https://wiki.openstreetmap.org/wiki/About_OpenStreetMap
[^2]: https://wiki.openstreetmap.org/wiki/Way
[^3]: https://en.wikipedia.org/wiki/Graph_(discrete_mathematics)
[^4]: https://wiki.openstreetmap.org/wiki/Highways
[^5]: https://wiki.openstreetmap.org/wiki/Key:highway
[^6]: https://osm2pgsql.org/doc/manual.html
[^7]: https://download.geofabrik.de/north-america.html
[^8]: https://github.com/kitahara-saneyuki/osm_parser/blob/main/atlas/dags/sql/03_parse_osm/04_routing_nodes.sql
[^9]: https://www.postgresql.org/docs/current/indexes-types.html
[^10]: https://github.com/kitahara-saneyuki/osm_parser/blob/eb6f1bbbf0d039904c9ddc8b76a8217d61d90fe3/atlas/dags/03_parse_osm.py#L21-L32
[^11]: https://cloud.tencent.com/developer/article/1734536
[^12]: https://www.dounaite.com/article/6254ffb57cc4ff68e6473f3f.html
[^13]: https://en.wikipedia.org/wiki/X86_Bit_manipulation_instruction_set
[^14]: https://zhuanlan.zhihu.com/p/100603507
[^15]: https://awesome-programming-books.github.io/algorithms/%E7%BC%96%E7%A8%8B%E7%8F%A0%E7%8E%91%EF%BC%88%E7%AC%AC2%E7%89%88%EF%BC%89.pdf
