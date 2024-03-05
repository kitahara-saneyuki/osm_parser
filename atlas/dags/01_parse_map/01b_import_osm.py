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
    db_pass,
    add_conn,
)
from utils.utils import (
    run_shell_command,
    regional_config,
    pbf_filename,
)


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
        for region in Variable.get(key="atlas_region_allowed", deserialize_json=True):
            region_json = open("config/regions/{region}.json".format(region=region))
            Variable.set(
                key=regional_config(region),
                value=json.load(region_json),
                serialize_json=True,
            )
    except FileNotFoundError:
        raise AirflowException("Regional configuration file not found!")


@task(task_id="02_create_pgpass")
def create_pgpass(default=False):
    pg_conn = Variable.get(key="conn_default", deserialize_json=True)
    atlas_region = "default"
    if not default:
        atlas_region = get_current_context()["dag_run"].conf["atlas_region"]
        pg_conn = Variable.get(key=regional_config(atlas_region), deserialize_json=True)
    try:
        pgpass_file = "config/{atlas_region}.pgpass".format(atlas_region=atlas_region)
        f = open(pgpass_file, "w")
        f.write(db_pass(pg_conn["db_conn"]))
        f.close()
        run_shell_command("chmod 600 {pgpass_file}".format(pgpass_file=pgpass_file))
    except Exception:
        pass


@task(task_id="03_create_db")
def create_db():
    atlas_region = get_current_context()["dag_run"].conf["atlas_region"]
    regional_cfg = Variable.get(
        key=regional_config(atlas_region), deserialize_json=True
    )
    regional_conn = regional_cfg["db_conn"]
    default_conn = Variable.get(key="conn_default", deserialize_json=True)["db_conn"]
    run_shell_command(
        "dags/01_parse_map/sql/01b_import_osm/01_create_db.sh {default_pgpass} {db_pgpass} {user} {password} {schema} \
                      {default_host} {default_user} {default_schema} {atlas_region}".format(
            default_pgpass="config/default.pgpass",
            db_pgpass="config/{atlas_region}.pgpass".format(atlas_region=atlas_region),
            user=regional_conn["user"],
            password=regional_conn["password"],
            schema=regional_conn["schema"],
            default_host=default_conn["host"],
            default_user=default_conn["user"],
            default_schema=default_conn["schema"],
            atlas_region=atlas_region,
        )
    )
    add_conn(db_conn(regional_cfg["db_conn"]))


@task(task_id="04_osm2pgsql")
def osm2pgsql():
    atlas_region = get_current_context()["dag_run"].conf["atlas_region"]
    regional_cfg = Variable.get(
        key=regional_config(atlas_region), deserialize_json=True
    )
    regional_conn = regional_cfg["db_conn"]
    run_shell_command(
        "dags/01_parse_map/sql/01b_import_osm/04_osm2pgsql.sh {db_pgpass} {pbf_path}{filename} \
            {schema} {user} {host}".format(
            db_pgpass="config/{atlas_region}.pgpass".format(atlas_region=atlas_region),
            pbf_path="data/{atlas_region}/osm/".format(atlas_region=atlas_region),
            filename=pbf_filename(atlas_region, regional_cfg),
            schema=regional_conn["schema"],
            user=regional_conn["user"],
            host=regional_conn["host"],
        )
    )


@task(task_id="05_trigger_downstream")
def trigger_downstream():
    atlas_region = get_current_context()["dag_run"].conf["atlas_region"]
    c = Client(None, None)
    c.trigger_dag(
        dag_id="01c_parse_osm",
        conf={"atlas_region": atlas_region},
        execution_date=datetime.now().astimezone(),
    )


with DAG(
    "01b_import_osm",
    default_args={
        "depends_on_past": False,
        "email": ["airflow@example.com"],
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    description="Init DB; import OSM PBF file from Geofabrik",
    schedule=timedelta(days=1),
    start_date=datetime(2021, 1, 1),
    catchup=False,
    tags=["atlas"],
) as dag:
    (
        set_variable()
        >> [create_pgpass(True), create_pgpass()]
        >> create_db()
        >> osm2pgsql()
        >> trigger_downstream()
    )
