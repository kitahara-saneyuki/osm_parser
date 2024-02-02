# OpenStreetMap Parsing

[中文](./docs/zh-CN/OSM-zh-CN.md) | English

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
- nodes ($V$, vertices), intersections of roads.
- edges ($E$, also labeled as arcs $A$), i.e., roads.

Each road segment has its own weight, depending on the requirements:
- speed
- time cost of travel
- length (distance)

In a weighted directed graph, nodes pointing to their own rings (e.g., a ring road in a residential area) are less important in routing and may cause undefined behavior of the routing algorithm.
Therefore we ignore them and use Directed Acyclic Graph (DAG) in routing.

## Osm2pgsql

We use osm2pgsql to parse the OSM data into a PostgreSQL database.
This is a tedious process, so we skip the discussion and refer to the osm2pgsql documentation[^6] for those interested.

We download the packaged `.OSM.pbf` map file from Geofabrik[^7].
Running osm2pgsql to parse OSM into PostgreSQL as raw data. What we cared about are the ways, as all the roads (highways) are served as ways.

## OSM way to edges

### Modeling nodes and Routing nodes

For ease of data storage, OSM road network is not a mathematical graph .
It is possible for OSM highways to cross intersections (a.k.a. nodes), so we need to cut OSM highways into edges, according to the road intersections (which are labeled as routing nodes in the SQL code).
On other hands, modeling nodes are the geometrical shape of the road.

Nodes are relatively simple data structures. We need to determine the required accuracy of coordinates based on our needs.

We assume earth as a perfect sphere (actually ellipsoid). As the radius of the earth is $6371km$, so its circumference, i.e., the length of longitude line, is about $6371km \times 2 \times \pi = 40009km$, divided by 360 degrees of latitude on the longitude line, we have the length of one degree is about 110km by napkin math.
The human walking scale is about 0.1m order of magnitude, which is sufficient for routing use, so it is easy to get that the accuracy of 6 decimal places can satisfy the demand ($10^{-6} \times 110km = 0.1m$).

### Determining the Routing nodes

Routing nodes are *nodes* in a mathematical *weighted directed graph* of road traffic network.
Roads are one-way arcs in a weighted directed graph, inscribing spatial relationships between nodes.

It is complicated to determine the routing nodes. To manage the complexity, we treat them case-by-case.

It is trivial that the two ends of each highway, the starting point and the ending point, must be the routing nodes.

We use a relatively quick SQL calculation [^8] to put all the modeling nodes of all roads into a single column, and then use an aggregation calculation to select the modeling nodes that have appeared simultaneously in __more than one road__.
If a modeling node appears in more than one road, it must be an intersection, i.e., a routing nodes.

It is not considered optimal by the author, just a feasible solution.

### Splitting ways and length calculation

This is a cumbersome calculation, and I have not found a solution that is feasible using SQL scripts alone. Readers are encouraged to explore on their own solutions.

I used python script to do the violent spliting, i.e., for each OSM way, loop through it one by one from the starting point, and if it encounters a routing node, it is considered as a separate road, i.e., an edge (arc) on the weighted directed graph.

Modeling nodes define the geometrical shape of ways.
We can compute the distance on the earth between any two points on the earth, i.e., the distance between two neighboring modeling nodes, as the length of the highway by the Haversine formula.
Summing the length of each segment on the way, we got the length of way.

## Performance optimization for PostgreSQL

PostgreSQL provides an extensive variety of types of indexes [^9], and we need to focus on two of them, their optimization of query performance on different scenarios in this application, and their underlying data structure.

SQL databases are the center of Internet applications, and optimizing the performance of database query in both time (query performance) and space (scalability) dimensions are most of our development.
NoSQL databases can handle the applications that cannot be optimized with traditional SQL databases. 
The simplest (yet most complex) use case is 12306.

### B+ tree index and its applications

The B+ tree[^11] is the most widely used index type in PostgreSQL, and supports a variety of comparison operations.
B+ tree in this project is mostly for high-performance sparse data query, such as this part of the code [^10], after testing, it is about 5 times faster than hash index.
Bitmap index scan[^12] speeds up the set operations[^14] dramatically by using instructions[^13] optimized in the x86 CPUs.

### GiST index and its applications

GiST indexes dramatically optimized the operations of querying the closest point or points in spatial proximity to a given point.

Selecting index specialized for coordinates reflects the basic principles of software development: __Select a right data structure for the application, and optimize it for what we need, performance, scalability, etc., based on the characteristics of the data itself.__
For specific practices, see a time-tested collection of essays on software development, Programming Pearls [^15].

In addition to B+ tree indexes and GiST indexes, Hash indexes and GIN indexes are also frequently used.
In addition, hstore is also a frequently used data structure.

[^1]: https://wiki.openstreetmap.org/wiki/About_OpenStreetMap
[^2]: https://wiki.openstreetmap.org/wiki/Way
[^3]: https://en.wikipedia.org/wiki/Graph_(discrete_mathematics)
[^4]: https://wiki.openstreetmap.org/wiki/Highways
[^5]: https://wiki.openstreetmap.org/wiki/Key:highway
[^6]: https://osm2pgsql.org/doc/manual.html
[^7]: https://download.geofabrik.de/north-america.html
[^8]: https://github.com/kitahara-saneyuki/osm_parser/blob/main/atlas/dags/sql/03_parse_osm/04_routing_nodes.sql#L15-L18
[^9]: https://www.postgresql.org/docs/current/indexes-types.html
[^10]: https://github.com/kitahara-saneyuki/OSM_parser/blob/eb6f1bbbf0d039904c9ddc8b76a8217d61d90fe3/atlas/dags/03_parse_OSM.py#L21-L32
[^11]: https://cloud.tencent.com/developer/article/1734536
[^12]: https://www.dounaite.com/article/6254ffb57cc4ff68e6473f3f.html
[^13]: https://en.wikipedia.org/wiki/X86_Bit_manipulation_instruction_set
[^14]: https://zhuanlan.zhihu.com/p/100603507
[^15]: https://awesome-programming-books.github.io/algorithms/%E7%BC%96%E7%A8%8B%E7%8F%A0%E7%8E%91%EF%BC%88%E7%AC%AC2%E7%89%88%EF%BC%89.pdf
