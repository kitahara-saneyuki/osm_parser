from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.models import Variable

from airflow.providers.postgres.operators.postgres import PostgresOperator


with DAG(
    "03_parse_osm",
    default_args={
        "depends_on_past": False,
        "email": ["airflow@example.com"],
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5)
    },
    description="Parse the OSM data",
    schedule=timedelta(days=1),
    start_date=datetime(2021, 1, 1),
    catchup=False,
    tags=["atlas"],
) as dag:
    clean_all_roads = PostgresOperator(
        task_id="01_clean_all_roads",
        postgres_conn_id=Variable.get(key="atlas_region").strip('\"'),
        sql="sql/02_parse_osm/01_clean_all_roads.sql",
    )

    traffic_mode_highways = "'" + "', '".join(Variable.get(key="traffic_mode_{mode}".format(
        mode=Variable.get(key="traffic_mode").strip('\"')
    ), deserialize_json=True)["highways"]) + "'"

    select_roads = PostgresOperator(
        task_id="02_select_roads",
        postgres_conn_id=Variable.get(key="atlas_region").strip('\"'),
        sql=f"""
            begin;
                update osm_highways set
                    maxspeed = cast((cast(maxspeed as smallint) / 1.609344) as smallint) WHERE maxspeed ~ E'^\\d+$';
                update osm_highways set
                    maxspeed = rtrim(maxspeed, ' mph') WHERE maxspeed !~ E'^\\d+$';
                update osm_highways set maxspeed = null WHERE maxspeed !~ E'^\\d+$';

                create table osm_roads as
                    select id, nodes, highway, access, oneway, name,
                        cast(maxspeed as smallint) as maxspeed,
                        nodes[1] as start_node,
                        nodes[array_length(nodes, 1)] as end_node,
                        nodes[2:array_length(nodes, 1) - 1] as middle_nodes,
                        tags from osm_highways
                where highway = any(array[{traffic_mode_highways}]);
            commit;
            """,
    )

    modelling_nodes = PostgresOperator(
        task_id="03_modelling_nodes",
        postgres_conn_id=Variable.get(key="atlas_region").strip('\"'),
        sql="sql/02_parse_osm/03_modelling_nodes.sql",
    )

    routing_nodes = PostgresOperator(
        task_id="04_routing_nodes",
        postgres_conn_id=Variable.get(key="atlas_region").strip('\"'),
        sql="sql/02_parse_osm/04_routing_nodes.sql",
    )

    new_edge_table = PostgresOperator(
        task_id="05_new_edge_table",
        postgres_conn_id=Variable.get(key="atlas_region").strip('\"'),
        sql="sql/02_parse_osm/05_new_edge_table.sql",
    )

    clean_all_roads >> \
    select_roads >> \
    modelling_nodes >> \
    routing_nodes >> \
    new_edge_table
