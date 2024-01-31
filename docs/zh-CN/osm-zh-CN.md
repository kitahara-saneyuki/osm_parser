# OpenStreetMap 路网剖析

中文 | [English](./docs/en-US/osm.md)

OpenStreetMap （下称 OSM ）[^1]使用折线[^2]这种数据结构储存道路交通网络。
我们关心其中的若干问题：

1.  OSM 道路交通图是否是一个数学意义上的图（ Graph ）[^3]？
1.  我们如何理解和分析 OSM 的 XML 数据？
1.  每条路段[^4]的基本属性，如
    1.  道路长度
    1.  通行速度，一般由道路类型[^5]决定
    1.  道路方向

我们将逐一剖析上述问题。

## 交通网络作为数学意义上的图

由于此处不需要引入寻路算法（ routing algorithm ，如 dijkstra ）的相关讨论，我们可以略过对图（ graph ）的数据结构表示的讨论。

道路交通网络，因为需要讨论每条边的长度，还需要引入极大量存在的单行道（ oneway ），包括几乎所有的高速公路和立交桥匝道我们都需要用单行道表示，因此我们一般将其表示为有向含权图（ weighted directed graph ）。

有向含权图 $G = (V, E)$ 包含两个主要元素，即
- 节点（ $V$,  vertices ），通俗来说可以理解成路口
- 边（ $E$,  edges ，也有人标记为弧（ $A$，即 arc ）），即道路。

每一条道路都有其权重（ weight ），根据需求，常用的有：
- 速度（ speed ）
- 通行耗时（ time cost ）
- 长度（ distance ）

有向含权图中，节点指向自己的环（如道路在居民区里终点的环路），在寻路中意义较小，而且可能会造成寻路算法的未定义行为。
因此我们略过它们，在寻路中使用有向无环图（ Directed Acyclic Graph ， DAG ）。

## OSM 路网数据的 SQL 表示： osm2pgsql

我们使用 osm2pgsql 将 osm 数据剖析为 PostgreSQL （下称 pg ）数据库。
这个过程较为繁琐，我们略过讨论，有兴趣的请自行翻阅 osm2pgsql 文档[^6] 。

我们从 Geofabrik[^7]下载已经被打包好了的 `.osm.pbf` 文件。
运行 osm2pgsql 剖析 osm 进入 pg 的是裸数据（ raw data ），我们关心其中的折线（ way ），因为所有的道路（ highway ）均以折线表示。

## OSM 道路的拆解

### 建模节点和寻路节点

osm 为了数据存储的方便，没有把路网剖析为数学意义上的图。
osm 的道路有可能会跨越节点（路口，两者可通用），因此我们需要按照实际出现的路口（在SQL代码中被我标记为寻路节点 routing nodes ），将osm道路（ highway ）切断成为图中的边（ edge ）。
与之相对应的，表示道路几何形状的点，我们称之为建模节点 modelling node 。

节点是相对简单的数据结构，只有两个属性，即经度和纬度，我们需要根据我们的需求确定对节点经纬度的精确度要求。

已知地球半径 r 约为 6371km ，因此其周长，亦即经线长度，约等于 `6371*2*3.14=40009km` ，除以经线上 360 个纬度，口算得到 1 度长度约为 110km。
对于人类步行而言，人类步行尺度大约在 0.1m 数量级，因此我们在日常生活中较少用到精度小于 0.1m （ 10cm ）以下的寻路精度，因此我们很容易得到，小数点后 6 位的精度即可满足需求（ $10^{-6} \times 110km = 0.1m$ ）。

### 判明寻路节点

我们可以把寻路节点理解为数学意义上图的节点。
道路作为有向含权图中的单向边，刻画了节点之间的空间关系。
与之相对的，节点也刻画了道路之间的空间关系，两者共同构建了作为有向含权图的道路交通网络。

判明寻路节点是有一定复杂度的，为了降低总体的计算量，我们使用分情况讨论。

易知，每条路的两端，起点和终点，必然为寻路节点。

之后的计算笔者认为并非最优，仅代表一个可行解。
我们使用一个相对快捷的 SQL 计算[^8]，拆解所有道路的建模节点成一个单独的列，然后使用聚合计算，选取在 __超过一条道路__ 中同时出现过的建模节点。
既然一建模节点在超过一条道路中出现，则其必然为路口，即寻路节点。

### 道路的拆解和长度的计算

这个计算较为繁琐，笔者并未找到一个单纯使用 SQL 脚本可行的解法，读者感兴趣可自行探索。

笔者使用的是 python 脚本进行暴力拆解，即，对每一条OSM折线（ way ），从起点开始逐个循环，如果遇到寻路节点，则认为其是一条单独的道路，即图上的边。

若干个建模节点连缀成一条折线，定义了道路的几何形状。
我们可以通过半正矢 Haversine 公式，计算地球上任意两点间在球面上的距离，即两个相邻建模节点间的距离，即为折线长度。
通过连缀一条道路上每条折线，计算这条道路上的折线长度总和，我们可以得到这条道路的长度（ length ）。

## pg 数据处理的性能优化

PostgreSQL 提供了极其博大精深的各种类型索引[^9]，我们需要重点讨论其中大概两种类型的索引，其对本应用中不同应用场景的检索性能的优化，及其能够成功优化的原理。

SQL 数据库作为互联网软件的中心，互联网应用软件的大部分开发流程，都是围绕着在时间（ performance ，即检索速度）和空间（ scalability ， 即可伸缩性）两个维度上优化数据库检索的性能，以及使用 NoSQL 数据库处理传统 SQL 数据库所不能优化的检索而展开的。
最简单（而又最庞杂）的应用案例，比如 12306 。

### B+ 树索引及其应用

B+ 树是 pg 应用最广泛的索引类型，支持多种比较操作。
本文不再赘述 B+ 树的原理[^11]，这部分知识留给读者自行探索，一般是本科数据库课程的基础内容。

B+ 树在本数据处理项目中的主要应用在于高速的稀疏检索，如这部分代码[^10]，经过试验，使用 B+ 树会比使用 hash 索引快5倍左右。
其秘诀在于位图索引扫描（ bitmap index scan ）[^12]，通过使用x86 CPU指令集层面优化过的位图操作（ bitmap operations ）[^13]，将集合计算[^14]大幅度加速。

### 空间 gist 索引及其应用

空间 gist 索引的原理此处不再赘述，在本应用中，其最大用途在于，以最快速度，检索到某一点空间距离最近的一个点或若干个点。

我们选择针对经纬度特化的索引，正体现了软件开发的基本原则：__根据应用选择恰当的数据结构，根据数据结构本身的特性，优化我们所需要的，性能、可扩展性，等等。__
具体实践可参考一本较老，但至今深受推崇的软件开发随笔集《编程珠玑》[^15]。

除了 B+ 树索引和空间 gist 索引之外，哈希（ hash ）索引和 gin 索引也是经常会用到的索引。
除此之外， hstore 也是经常要用到的数据结构。

[^1]: https://wiki.openstreetmap.org/wiki/About_OpenStreetMap
[^2]: https://wiki.openstreetmap.org/wiki/Way
[^3]: https://www.cnblogs.com/wangyingli/p/5974508.html
[^4]: https://wiki.openstreetmap.org/wiki/Highways
[^5]: https://wiki.openstreetmap.org/wiki/Key:highway
[^6]: https://osm2pgsql.org/doc/manual.html
[^7]: https://download.geofabrik.de/north-america.html
[^8]: https://github.com/kitahara-saneyuki/osm_parser/blob/main/atlas/dags/sql/03_parse_osm/04_routing_nodes.sql
[^9]: https://developer.aliyun.com/article/111793
[^10]: https://github.com/kitahara-saneyuki/osm_parser/blob/eb6f1bbbf0d039904c9ddc8b76a8217d61d90fe3/atlas/dags/03_parse_osm.py#L21-L32
[^11]: https://cloud.tencent.com/developer/article/1734536
[^12]: https://www.dounaite.com/article/6254ffb57cc4ff68e6473f3f.html
[^13]: https://en.wikipedia.org/wiki/X86_Bit_manipulation_instruction_set
[^14]: https://zhuanlan.zhihu.com/p/100603507
[^15]: https://awesome-programming-books.github.io/algorithms/%E7%BC%96%E7%A8%8B%E7%8F%A0%E7%8E%91%EF%BC%88%E7%AC%AC2%E7%89%88%EF%BC%89.pdf
