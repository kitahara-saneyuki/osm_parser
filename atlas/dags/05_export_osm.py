from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.decorators import task
from airflow.operators.python import get_current_context
from airflow.models import Variable

from utils.db import PostgresOperator
from utils.utils import run_shell_command, regional_config


@task(task_id="02_copy2csv")
def copy2csv():
    atlas_region = get_current_context()["dag_run"].conf["atlas_region"]
    regional_cfg = Variable.get(
        key=regional_config(atlas_region), deserialize_json=True
    )
    regional_conn = regional_cfg["db_conn"]
    run_shell_command(
        "dags/sql/05_export_osm/02_copy2csv.sh {db_pgpass} data/{atlas_region}/output \
            {host} {user} {schema}".format(
            db_pgpass="config/{atlas_region}.pgpass".format(atlas_region=atlas_region),
            atlas_region=atlas_region,
            host=regional_conn["host"],
            user=regional_conn["user"],
            schema=regional_conn["schema"],
        )
    )


with DAG(
    "05_export_osm",
    default_args={
        "depends_on_past": False,
        "email": ["airflow@example.com"],
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    description="Export road network as graph CSV",
    schedule=timedelta(days=1),
    start_date=datetime(2021, 1, 1),
    catchup=False,
    tags=["atlas"],
) as dag:
    generate_arcs = PostgresOperator(
        task_id="01_generate_arcs",
        postgres_conn_id="{{ dag_run.conf['atlas_region'] }}",
        sql="sql/05_export_osm/01_generate_arcs.sql",
    )
    generate_arcs >> copy2csv()
