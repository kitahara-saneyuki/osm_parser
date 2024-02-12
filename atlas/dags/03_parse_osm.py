from __future__ import annotations

import csv
import gc
import logging
import time

from datetime import datetime, timedelta

from airflow import DAG
from airflow.api.client.local_client import Client
from airflow.decorators import task
from airflow.operators.python import get_current_context
from airflow.models import Variable

from utils.db import PGConn, PostgresOperator
from utils.haversine import haversine_length
from utils.utils import run_shell_command, regional_config


select_all_roads = """
    SELECT id, nodes, start_node, end_node
    FROM osm_roads
    ORDER BY id
    LIMIT {limit}
    OFFSET {offset}
"""
select_latlon = """
    SELECT {id_col}, latitude, longitude
    FROM {table}
    WHERE {id_col} = any(array{id_arr})
"""


@task(task_id="06_cut_roads")
def cut_roads():
    atlas_region = get_current_context()["dag_run"].conf["atlas_region"]
    pg_conn = PGConn(
        Variable.get(key=regional_config(atlas_region), deserialize_json=True)[
            "db_conn"
        ]
    )
    with open(
        "data/{atlas_region}/temp/edges.csv".format(atlas_region=atlas_region),
        "w",
        newline="\n",
    ) as csvfile:
        csv_writer = csv.writer(
            csvfile, delimiter="\x02", quotechar="\x03", quoting=csv.QUOTE_MINIMAL
        )
        offset = 0
        chunk = pg_conn.run_query(
            select_all_roads.format(
                limit=int(Variable.get(key="sql_chunk")), offset=offset
            ),
        )
        logging.info(
            "{:>10} {:>10} {:>10} {:<6} {:>7} {:<6} {:>10} {:<8} {:>10}".format(
                "offset",
                "# nodes",
                "m. n. s",
                "m. n. μs",
                "r. n. s",
                "r. n. μs",
                "roads s",
                "road μs",
                "total s",
            )
        )
        while chunk:
            now = time.time_ns()
            offset += int(Variable.get(key="sql_chunk"))
            set_nodes = set()
            for road in chunk:
                set_nodes.update(road["nodes"])
            global_nodes = pg_conn.run_query_map(
                select_latlon,
                "id",
                "osm_modelingnodes",
                list(set_nodes),
            )
            t1 = (time.time_ns() - now) / 1000

            now = time.time_ns()
            routing_nodes = pg_conn.run_query_map(
                select_latlon,
                "osm_id",
                "osm_routingnodes",
                list(set_nodes),
            )
            t2 = (time.time_ns() - now) / 1000

            now = time.time_ns()
            gc.collect()
            for road in chunk:
                nodes = road["nodes"]
                # Step 1: calculate the haversine length of the entire osm_way
                total_edge_length = 0
                osm_way_length = haversine_length(nodes, global_nodes)
                if osm_way_length == 0:
                    continue
                last_node = 0
                for i in range(0, len(nodes)):
                    if i != 0 and nodes[i] in routing_nodes:
                        split_segment = nodes[last_node: i + 1]
                        # Step 2: calculate the haversine length of each edge
                        edge_length = haversine_length(split_segment, global_nodes)

                        # Step 3: insert the cut edge into the database
                        way_start_offset = total_edge_length
                        way_end_offset = total_edge_length + edge_length
                        csv_writer.writerow(
                            [
                                "{" + ",".join(map(str, split_segment)) + "}",
                                way_start_offset,
                                way_end_offset,
                                osm_way_length,
                                split_segment[0],
                                split_segment[-1],
                                road["id"],
                            ]
                        )
                        total_edge_length += edge_length
                        last_node = i
                # Step 2.1 (for check): calculate the haversine length of the entire osm_way
                if abs(total_edge_length - osm_way_length) / osm_way_length > 0.00001:
                    logging.info(
                        "Failing! -- total edge length {total_edge_length} != osm way length {osm_way_length}".format(
                            total_edge_length=total_edge_length,
                            osm_way_length=osm_way_length,
                        )
                    )
            chunk = pg_conn.run_query(
                select_all_roads.format(
                    limit=int(Variable.get(key="sql_chunk")), offset=offset
                ),
            )
            t3 = (time.time_ns() - now) / 1_000
            if chunk:
                logging.info(
                    "{:>10} {:>10} {:>10.2f} {:<6.2f} {:>10.2f} {:<6.2f} {:>10.2f} {:<8.2f} {:>10.2f}".format(
                        offset,
                        len(set_nodes),
                        t1 / 1_000_000,
                        t1 / len(global_nodes),
                        t2 / 1_000_000,
                        t2 / len(routing_nodes),
                        t3 / 1_000_000,
                        t3 / len(chunk),
                        (t1 + t2 + t3) / 1_000_000,
                    )
                )


@task(task_id="07_import_edges")
def import_edges():
    atlas_region = get_current_context()["dag_run"].conf["atlas_region"]
    regional_cfg = Variable.get(
        key=regional_config(atlas_region), deserialize_json=True
    )
    regional_conn = regional_cfg["db_conn"]
    run_shell_command(
        "dags/sql/03_parse_osm/07_import_edges.sh {db_pgpass} data/{atlas_region}/temp \
            {host} {user} {schema}".format(
            db_pgpass="config/{atlas_region}.pgpass".format(atlas_region=atlas_region),
            atlas_region=atlas_region,
            host=regional_conn["host"],
            user=regional_conn["user"],
            schema=regional_conn["schema"],
        )
    )


def assign_maxspeed(traffic_mode, traffic_mode_highways):
    return "begin;\n" + "\n".join([
        "update osm_edges set maxspeed = {maxspeed} where highway = '{highway}' {nullify_maxspeed};".format(
            maxspeed=maxspeed,
            highway=highway,
            nullify_maxspeed="and maxspeed is null" if traffic_mode != "pedestrian" else ""
        ) for highway, maxspeed in traffic_mode_highways.items()
    ]) + "commit;\n"


@task(task_id="10_trigger_downstream")
def trigger_downstream():
    atlas_region = get_current_context()["dag_run"].conf["atlas_region"]
    c = Client(None, None)
    c.trigger_dag(
        dag_id="10_export_osm",
        conf={"atlas_region": atlas_region},
        execution_date=datetime.now().astimezone(),
    )


with DAG(
    "03_parse_osm",
    default_args={
        "depends_on_past": False,
        "email": ["airflow@example.com"],
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    description="Parse the OSM data",
    schedule=timedelta(days=1),
    start_date=datetime(2021, 1, 1),
    catchup=False,
    tags=["atlas"],
) as dag:
    traffic_mode_highways = {}
    try:
        traffic_mode = Variable.get("traffic_mode", default_var="road").strip('"')
        traffic_mode_highways = Variable.get(
            key="traffic_mode_{traffic_mode}".format(traffic_mode=traffic_mode),
            default_var={"highways": {}},
            deserialize_json=True,
        )["highways"]
    except Exception as exc:
        raise exc
    traffic_mode_highways_str = "'" + "', '".join(traffic_mode_highways.keys()) + "'"

    clean_all_roads = PostgresOperator(
        task_id="01_clean_all_roads",
        postgres_conn_id="{{ dag_run.conf['atlas_region'] }}",
        sql="sql/03_parse_osm/01_clean_all_roads.sql",
    )

    select_roads = PostgresOperator(
        task_id="02_select_roads",
        postgres_conn_id="{{ dag_run.conf['atlas_region'] }}",
        sql=f"""
            begin;
                drop table if exists osm_roads;
                create table osm_roads as
                    select id, nodes, highway, access, oneway, name,
                        cast(maxspeed as smallint) as maxspeed,
                        nodes[1] as start_node,
                        nodes[array_length(nodes, 1)] as end_node,
                        nodes[2:array_length(nodes, 1) - 1] as middle_nodes,
                        tags from osm_highways
                where highway = any(array[{traffic_mode_highways_str}]);

                drop table if exists osm_highways;
                create index osm_roads_idx on osm_roads using btree(id);
                create index osm_roads_nodes_idx on osm_roads using gin(nodes);
            commit;
            """,
    )

    modeling_nodes = PostgresOperator(
        task_id="03_modeling_nodes",
        postgres_conn_id="{{ dag_run.conf['atlas_region'] }}",
        sql="sql/03_parse_osm/03_modeling_nodes.sql",
    )

    routing_nodes = PostgresOperator(
        task_id="04_routing_nodes",
        postgres_conn_id="{{ dag_run.conf['atlas_region'] }}",
        sql="sql/03_parse_osm/04_routing_nodes.sql",
    )

    new_edge_table = PostgresOperator(
        task_id="05_new_edge_table",
        postgres_conn_id="{{ dag_run.conf['atlas_region'] }}",
        sql="sql/03_parse_osm/05_new_edge_table.sql",
    )

    post_processing = PostgresOperator(
        task_id="08_post_processing",
        postgres_conn_id="{{ dag_run.conf['atlas_region'] }}",
        sql="sql/03_parse_osm/08_post_processing.sql",
    )

    assign_maxspeed = PostgresOperator(
        task_id="09_assign_maxspeed",
        postgres_conn_id="{{ dag_run.conf['atlas_region'] }}",
        sql=assign_maxspeed(traffic_mode, traffic_mode_highways),
    )

    (
        clean_all_roads
        >> select_roads
        >> modeling_nodes
        >> routing_nodes
        >> new_edge_table
        >> cut_roads()
        >> import_edges()
        >> post_processing
        >> assign_maxspeed
        >> trigger_downstream()
    )
