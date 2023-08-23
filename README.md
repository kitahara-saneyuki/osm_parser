# OSM Routing Engine

[![Lint check](https://github.com/vincentj93/osm_routing/actions/workflows/lint.yml/badge.svg)](https://github.com/vincentj93/osm_routing/actions/workflows/lint.yml)
[![Atlas tests](https://github.com/vincentj93/osm_routing/actions/workflows/atlas.yml/badge.svg)](https://github.com/vincentj93/osm_routing/actions/workflows/atlas.yml)

1. [Getting started](#getting-started)
    1. [Atlas](#atlas)
    1. [Mercury](#mercury)
1. [Building blocks](#building-blocks)
1. [ETL Design Principles](#etl-design-principles)
1. [Project Roadmap](#project-roadmap)
1. [Contributing](#contributing)

## Getting started

### Atlas

#### Set up Atlas

Prerequisite: Docker

1. Clone the repo
1. Under the project folder, run the shell command below (the initialization would take a few minutes)

    ```sh
    make init
    make up
    ```

1. Now the Airflow GUI console is accessible at <http://localhost:8080/>
    1. Airflow user name and password is set by default as `airflow:airflow`, this can be changed in the `docker-compose.yaml`
    1. PostgreSQL database user name and password is set as above, this can be changed in the `atlas/config/commons.json`
1. Also you can use the Airflow REST API or CLI commands to trigger jobs
1. Usually you will need to unpause the Airflow jobs by `make unpause`, before trigger the first Airflow job
1. To verify the integrity of Atlas codebase, you can use `make test`

#### Add new regions / transportation modes in Atlas

Atlas has two preset regions in the `atlas/config` folder: **Bristol, UK** (used for automated testing) and **Washington, US**.
Also, two preset transportation modes, **road** and **pedestrian** are provided.
It's very simple to add your own regions and / or transportation modes in Atlas:

- Create your own configuration JSON file in the folder `atlas/config/regions` and / or `atlas/config/modes`,
- Add your own regions / modes in the `atlas/config/commons.json`, field `atlas_region_allowed` or `traffic_mode_allowed`, so the new configuration can be found by the Airflow DAGs.

#### Trigger Atlas pipeline

After your region is set up, in the terminal, run

```sh
make run region=<region>
```

You can also trigger the pipeline through GUI or REST API.

#### VSCode Python Interpreter Set up

First we need to install Python 3.7 by `make python37` (the script is tested under Debian 12).
Then run:

```sh
python3.7 -m virtualenv -p python3.7 venv
source venv/bin/activate
pip install -r requirements-venv.txt
```

Select the Python interpreter in the bottom-right corner of VSCode window, and voila.

### Mercury

(Under construction)

## Building blocks

1. Atlas: Parse OSM data into a _Graph_ of transportation network.
    1. Tech stack: Python 3, Airflow 2.6, PostgreSQL 13 / PostGIS, osm2pgsql
1. Mercury: Route planning in the transportation network. Accepts REST API call.
    1. Tech stack: Rust, Rocket
    1. Reference: Customizable Contraction Hierarchies. Julian Dibbelt, Ben Strasser, and Dorothea Wagner. ACM Journal of Experimental Algorithmics, 2016.
1. Phoebe: Microservice layer of Mercury, for path and isochrone rendering
    1. Tech stack: Python, Django
1. Dionysus: A simple GUI for visualizing everything
    1. Tech stack: Typescript, React, Leaflet
1. Idyia (Planned): ElasticSearch connector for Geocoding
    1. Tech stack: PostgreSQL, Kafka, kSQL, Debezium, ElasticSearch

## ETL Design Principles

1. Idempotence
1. Modularity
1. Atomicity
1. Change Detection and Increment
1. Scalability
1. Error Detection and Data Validation
1. Recovery and Restartability

## Project Roadmap

1. [ ] CCH Algorithm API
    1. [ ] 1-1 routing
    1. [ ] Path rendering
    1. [ ] Matrix routing
    1. [ ] Isochrone rendering
    1. [ ] SIMD computing
1. [ ] Visualized routing
1. [ ] Helm Chart
1. [ ] Incremental processing
1. [x] Automated testing

## Contributing

Contributions are absolutely, positively welcome and encouraged! Contributions come in many forms. You could:

1. Submit a feature request or bug report as an issue.
1. Ask for improved documentation as an issue.
1. Comment on issues that require feedback.
1. Contribute code via pull requests.

We aim to keep code quality at the highest level. This means that any code you contribute must be:

1. Commented: Complex and non-obvious functionality must be properly commented.
1. Documented: Public items must have doc comments with examples, if applicable.
1. Styled: Your code's style should match the existing and surrounding code style.
1. Simple: Your code should accomplish its task as simply and idiomatically as possible.
1. Tested: You must write (and pass) convincing tests for any new functionality.
1. Focused: Your code should do what it's supposed to and nothing more.

All pull requests are code reviewed and tested by the CI.

## Reference

1. [14 Rules To Succeed With Your ETL Project](https://refinepro.com/blog/14-rules-for-successful-ETL/)
