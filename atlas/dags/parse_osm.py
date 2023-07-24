from __future__ import annotations

import logging
import json
import subprocess

from datetime import datetime, timedelta

from airflow import DAG, AirflowException
from airflow.decorators import task
from airflow.models import Variable
from airflow.models.connection import Connection

from airflow.providers.postgres.operators.postgres import PostgresOperator

@task
def variable_set():
    common_config = open("config/commons.json")
    for k, v in json.load(common_config).items():
        Variable.set(key=k, value=v, serialize_json=True)
    try:
        atlas_region = Variable.get(key="atlas_region").strip('\"')
        regional_config = open("config/regions/{atlas_region}.json".format(atlas_region=atlas_region))
        Variable.set(key=atlas_region, value=json.load(regional_config), serialize_json=True)
    except FileNotFoundError as exc:
        raise AirflowException('Regional configuration file not found!')

@task
def download_pbf():
    atlas_region = Variable.get(key="atlas_region").strip('\"')
    regional_config = Variable.get(key=atlas_region, deserialize_json=True)
    filename = "{atlas_region}-latest.osm.pbf".format(atlas_region=atlas_region)
    subprocess.run([
        "curl -o {pbf_path}{filename} {download_server_url}{download_pbf_url}{filename}".format(
            pbf_path="data/osm/",
            download_server_url=Variable.get(key="download_server_url"),
            download_pbf_url=regional_config["download_pbf_url"],
            filename=filename,
        )],
        shell=True
    )

with DAG(
    "parse_osm",
    # These args will get passed on to each operator
    # You can override them on a per-task basis during operator initialization
    default_args={
        "depends_on_past": False,
        "email": ["airflow@example.com"],
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
        # 'queue': 'bash_queue',
        # 'pool': 'backfill',
        # 'priority_weight': 10,
        # 'end_date': datetime(2016, 1, 1),
        # 'wait_for_downstream': False,
        # 'sla': timedelta(hours=2),
        # 'execution_timeout': timedelta(seconds=300),
        # 'on_failure_callback': some_function, # or list of functions
        # 'on_success_callback': some_other_function, # or list of functions
        # 'on_retry_callback': another_function, # or list of functions
        # 'sla_miss_callback': yet_another_function, # or list of functions
        # 'trigger_rule': 'all_success'
    },
    description="Atlas DAG",
    schedule=timedelta(days=1),
    start_date=datetime(2021, 1, 1),
    catchup=False,
    tags=["atlas"],
) as dag:
    
    drop_old_tables = PostgresOperator(
        task_id="drop_old_tables",
        postgres_conn_id="postgres",
        sql="sql/drop_old_tables.sql",
    )

    variable_set() >> [drop_old_tables, download_pbf()]
