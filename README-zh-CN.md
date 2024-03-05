# Atlas：OpenStreetMap 数据剖析器

[![Lint check](https://github.com/kitahara-saneyuki/osm_parser/actions/workflows/lint.yml/badge.svg)](https://github.com/kitahara-saneyuki/osm_parser/actions/workflows/lint.yml)
[![Atlas tests](https://github.com/kitahara-saneyuki/osm_parser/actions/workflows/atlas.yml/badge.svg)](https://github.com/kitahara-saneyuki/osm_parser/actions/workflows/atlas.yml)
[![Wiki pages](https://github.com/kitahara-saneyuki/osm_parser/actions/workflows/docs.yml/badge.svg)](https://github.com/kitahara-saneyuki/osm_parser/actions/workflows/docs.yml)

中文 | [English](./README.md)

1.  [设计目标](#设计目标)
1.  [开始工作](#开始工作)
1.  [项目路线图](#项目路线图)
1.  [如何成为贡献者](#如何成为贡献者)

## 设计目标

一个

- 易于配置的
- 易于扩展的
- 易于维护的
- 易于伸缩的
- 健壮的

用于 OpenStreetMap 的解析器，为在 OpenStreetMap 道路网络中操纵数据提供最佳体验。

## 开始工作

### 安装 Atlas

1.  安装 Docker
1.  下载 repo
1.  在项目文件夹下运行 `make up`（初始化需要几分钟时间）
1.  现在可以访问 Airflow GUI 控制台，网址是 <http://localhost:8080/>
    1.  Airflow 用户名和密码默认设置为 `airflow:airflow`，可以在 `docker-compose.yaml` 中更改
    1.  PostgreSQL 数据库用户名和密码设置如上，可在 `atlas/config/commons.json` 中更改
1.  您可以使用 Airflow REST API 或 CLI 命令来启动任务
1.  通常，在启动第一个 Airflow 任务之前，您需要通过 `make unpause` 使 Airflow 任务可用。
1.  要验证 Atlas 代码库的完整性，可以使用 `make test` 来进行验证。

### 在 Atlas 中添加新区域/交通模式

Atlas 的 `atlas/config` 文件夹中提供了两个预设区域： **英国布里斯托尔**（用于自动测试）和 **美国华盛顿州** 。
此外，还提供了两种预设交通模式： **公路** （ `road` ） 和 **步行** （ `pedestrian` ） 。
在 Atlas 中添加自己的地区和/或交通模式非常简单：

- 在 `atlas/config/regions` 和/或 `atlas/config/modes` 文件夹中创建自己的配置 JSON 文件、
- 在 `atlas/config/commons.json` 的 `atlas_region_allowed` 或 `traffic_mode_allowed` 字段中添加您自己的区域/模式，这样 Airflow DAG 就能找到新配置。

### 执行 Atlas 任务并输出 CSV 格式

设置完成后，在终端运行

```sh
make run step=<step> region=<region>
```

您也可以通过 GUI 或 REST API 执行任务。

输出可在 `data/<region>/output` 文件夹中找到，其中包含 3 个 CSV 文件：

- 节点：包含两列数据：每个节点的经纬度坐标。列号为 `node_id` （从 0 开始）。
- 图：包含三列数据。我们通过有向无环图（DAG）实现交通网络。有向无环图中的每条弧，前两列为其起点和终点的 `node_id`，第三列为其 “时间成本”（单位毫秒），即有向无环图中每条弧的“权重”。

### VSCode Python 解释器设置

首先，我们需要安装 Python 3.8
- 如果您使用 Ubuntu ，推荐使用 `sudo add-apt-repository ppa:deadsnakes/ppa` 安装 Python 3.8

然后运行

```sh
sudo apt-get install python3.8-distutils libsasl2-dev python3.8-dev libldap2-dev libssl-dev
python3.8 -m virtualenv -p python3.8 venv
source venv/bin/activate
pip install -r atlas/requirements-venv.txt
```

点击 VSCode 窗口右下角的 Python 解释器，选择 `venv/bin/python3.8` 即可。

## 项目路线图

1.  [x] 自动测试
1.  [ ] 并行处理

## 如何成为贡献者

我们十分欢迎贡献者！贡献有多种形式。您可以

1.  提交功能请求或错误报告作为 Issue 。
1.  以 Issue 的形式要求改进文档。
1.  对需要反馈的 Issue 发表评论
1.  通过 Pull Request 贡献代码。

我们希望把代码质量保持在最高水平。这意味着，您贡献的任何代码都需要

1.  有注释：复杂和非显而易见的功能必须有适当的注释。
1.  文档：公共项目必须有文档注释，必要的话须附有示例。
1.  风格：您的代码风格应与现有和上下文代码风格相匹配。
1.  简洁：您的代码应尽可能简单、习以为常地完成任务。
1.  经过测试：您需要为任何新功能编写（并通过）令人信服的测试。
1.  功能专一：您的代码应该完成它应该完成的任务，仅此而已。

所有 Pull Request 都将通过持续集成进行代码审查和测试。

此外，在代码评审中，我们将遵循 ETL 设计原则：

1.  幂等性
1.  模块性
1.  原子性
1.  变化检测和增量
1.  可伸缩性
1.  错误检测和数据验证
1.  可恢复性和可重启性

## Reference

1.  [14 Rules To Succeed With Your ETL Project](https://refinepro.com/blog/14-rules-for-successful-ETL/)
