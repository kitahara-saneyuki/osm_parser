from __future__ import annotations

import json

from datetime import datetime, timedelta

from airflow import DAG, AirflowException
from airflow.api.client.local_client import Client
from airflow.decorators import task
from airflow.operators.python import get_current_context
from airflow.models import Variable

from utils.db import PostgresOperator


@task(task_id="01_set_variable")
def set_variable():
    try:
        for mode in Variable.get(key="traffic_mode_allowed", deserialize_json=True):
            mode_json = open("config/modes/{mode}.json".format(mode=mode))
            Variable.set(
                key="traffic_mode_{mode}".format(mode=mode),
                value=json.load(mode_json),
                serialize_json=True,
            )
    except FileNotFoundError:
        raise AirflowException("Regional configuration file not found!")


def sql_maxspeed(traffic_mode, traffic_mode_highways):
    return (
        "begin;\n"
        + "\n".join(
            [
                "update osm_edges set maxspeed = {maxspeed} where highway = '{highway}' {nullify_maxspeed};".format(
                    maxspeed=maxspeed,
                    highway=highway,
                    nullify_maxspeed=(
                        "and maxspeed is null" if traffic_mode != "pedestrian" else ""
                    ),
                )
                for highway, maxspeed in traffic_mode_highways.items()
            ]
        )
        + "commit;\n"
    )


@task(task_id="10_trigger_downstream")
def trigger_downstream():
    atlas_region = get_current_context()["dag_run"].conf["atlas_region"]
    c = Client(None, None)
    c.trigger_dag(
        dag_id="10_export_csv",
        conf={"atlas_region": atlas_region},
        execution_date=datetime.now().astimezone(),
    )


with DAG(
    "01d_assign_maxspeed",
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

    assign_maxspeed = PostgresOperator(
        task_id="02_assign_maxspeed",
        postgres_conn_id="{{ dag_run.conf['atlas_region'] }}",
        sql=sql_maxspeed(traffic_mode, traffic_mode_highways),
    )

    (
        set_variable()
        >> assign_maxspeed
        >> trigger_downstream()
    )
