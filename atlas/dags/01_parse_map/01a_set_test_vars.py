from __future__ import annotations

import json

from datetime import datetime, timedelta

from airflow import DAG, AirflowException

from airflow.api.client.local_client import Client
from airflow.decorators import task
from airflow.operators.python import get_current_context
from airflow.models import Variable

from utils.db import (
    db_conn,
    add_conn,
)


@task(task_id="01_set_variable")
def set_variable():
    common_config = open("config/test.json")
    for k, v in json.load(common_config).items():
        Variable.set(key=k, value=v, serialize_json=True)
    add_conn(
        db_conn(Variable.get(key="conn_default", deserialize_json=True)["db_conn"])
    )


@task(task_id="02_trigger_downstream")
def trigger_downstream():
    atlas_region = get_current_context()["dag_run"].conf["atlas_region"]
    c = Client(None, None)
    c.trigger_dag(
        dag_id="01b_import_osm",
        conf={"atlas_region": atlas_region},
        execution_date=datetime.now().astimezone(),
    )


with DAG(
    "01a_set_test_vars",
    default_args={
        "depends_on_past": False,
        "email": ["airflow@example.com"],
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    description="Set vars for testing",
    schedule=timedelta(days=1),
    start_date=datetime(2021, 1, 1),
    catchup=False,
    tags=["atlas"],
) as dag:
    (
        set_variable()
        >> trigger_downstream()
    )
