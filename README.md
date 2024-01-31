# Atlas: an OpenStreetMap parser

[![Lint check](https://github.com/kitahara-saneyuki/osm_parser/actions/workflows/lint.yml/badge.svg)](https://github.com/kitahara-saneyuki/osm_parser/actions/workflows/lint.yml)
[![Atlas tests](https://github.com/kitahara-saneyuki/osm_parser/actions/workflows/atlas.yml/badge.svg)](https://github.com/kitahara-saneyuki/osm_parser/actions/workflows/atlas.yml)
[![Wiki pages](https://github.com/kitahara-saneyuki/osm_parser/actions/workflows/docs.yml/badge.svg)](https://github.com/kitahara-saneyuki/osm_parser/actions/workflows/docs.yml)

[中文](./README-zh-CN.md) | English

1.  [Project Goals](#project-goals)
1.  [Getting started](#getting-started)
1.  [Project Roadmap](#project-roadmap)
1.  [Contributing](#contributing)

## Design Goals

An

- easily configurable
- easily extendable
- easily maintainable
- easily scalable
- robust

parser for OpenStreetMap, for the best experience in data manipulating in OpenStreetMap road network.

## Getting started

### Set up Atlas

1.  Prerequisite: Install Docker
1.  Clone the repo
1.  Under the project folder, run `make up` (the initialization would take a few minutes)
1.  Now the Airflow GUI console is accessible at <http://localhost:8080/>
    1.  Airflow user name and password is set by default as `airflow:airflow`, this can be changed in the `docker-compose.yaml`
    1.  PostgreSQL database user name and password is set as above, this can be changed in the `atlas/config/commons.json`
1.  Also you can use the Airflow REST API or CLI commands to trigger jobs
1.  Usually you will need to make the Airflow jobs available by `make unpause`, before trigger the first Airflow job
1.  To verify the integrity of Atlas codebase, you can use `make test`

### Add new regions / transportation modes in Atlas

Atlas has provided two preset regions in the `atlas/config` folder: **Bristol, UK** (used for automated testing) and **Washington, US**.
Also, two preset transportation modes, **road** and **pedestrian** are provided.
It's very simple to add your own regions and / or transportation modes in Atlas:

- Create your own configuration JSON file in the folder `atlas/config/regions` and / or `atlas/config/modes`,
- Add your own regions / modes in the `atlas/config/commons.json`, field `atlas_region_allowed` or `traffic_mode_allowed`, so the new configuration can be found by the Airflow DAGs.

### Trigger Atlas job, and output CSV format

After your region is set up, in the terminal, run

```sh
make run region=<region>
```

You can also trigger the job through GUI or REST API.

The output can be found at `data/<region>/output` folder, with 3 CSV files:

- `node`: 2 columns, latitude / longitude coordinate for each node. The column number is `node_id` (start from 0).
- `graph`: 3 columns: head -> tail of `node_id`, representing each _arc_ of the _directed acyclic graph_(DAG) for the transportation network, and the `time_cost` (in milliseconds), serving as _weight_ of each arc in the DAG.

### VSCode Python Interpreter Set up

First we need to install Python 3.7:
- For Debian 12 users, you can use our script `make python37`
- For Ubuntu users, it's recommended to use `sudo add-apt-repository ppa:deadsnakes/ppa`

Then run:

```sh
sudo apt-get install python3.7-distutils libsasl2-dev python3.7-dev libldap2-dev libssl-dev
python3.7 -m virtualenv -p python3.7 venv
source venv/bin/activate
pip install -r requirements-venv.txt
```

Select `venv/bin/python3.7` as the Python interpreter in the bottom-right corner of VSCode window, and voila.

## Project Roadmap

1.  [x] Automated testing
1.  [ ] Parallel processing

## Contributing

Contributions are absolutely, positively welcome and encouraged! Contributions come in many forms. You could:

1.  Submit a feature request or bug report as an issue.
1.  Ask for improved documentation as an issue.
1.  Comment on issues that require feedback.
1.  Contribute code via pull requests.

We aim to keep code quality at the highest level. This means that any code you contribute must be:

1.  Commented: Complex and non-obvious functionality must be properly commented.
1.  Documented: Public items must have doc comments with examples, if applicable.
1.  Styled: Your code's style should match the existing and surrounding code style.
1.  Simple: Your code should accomplish its task as simply and idiomatically as possible.
1.  Tested: You must write (and pass) convincing tests for any new functionality.
1.  Focused: Your code should do what it's supposed to and nothing more.

All pull requests are code reviewed and tested by the CI.

Also, during code review, we will follow the ETL design principles:

1.  Idempotence
1.  Modularity
1.  Atomicity
1.  Change Detection and Increment
1.  Scalability
1.  Error Detection and Data Validation
1.  Recovery and Restartability

## Reference

1.  [14 Rules To Succeed With Your ETL Project](https://refinepro.com/blog/14-rules-for-successful-ETL/)
