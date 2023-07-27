from __future__ import annotations

import json

from datetime import datetime, timedelta

from airflow import DAG, AirflowException
from airflow.decorators import task
from airflow.models import Variable

from utils.utils import (run_shell_command, regional_config, db_conn, db_pass, add_conn)


@task
def set_variable():
    common_config = open("config/commons.json")
    for k, v in json.load(common_config).items():
        Variable.set(key=k, value=v, serialize_json=True)
    add_conn(db_conn(Variable.get(key="conn_default", deserialize_json=True)["db_conn"]))
    try:
        atlas_region = Variable.get(key="atlas_region").strip('\"')
        regional_cfg = open("config/regions/{atlas_region}.json".format(atlas_region=atlas_region))
        Variable.set(key=regional_config(atlas_region), value=json.load(regional_cfg), serialize_json=True)
    except FileNotFoundError as exc:
        raise AirflowException('Regional configuration file not found!')


@task
def download_pbf():
    atlas_region = Variable.get(key="atlas_region").strip('\"')
    regional_cfg = Variable.get(key=regional_config(atlas_region), deserialize_json=True)
    filename = "{atlas_region}-latest.osm.pbf".format(atlas_region=atlas_region)
    run_shell_command("curl -o {pbf_path}{filename} {download_server_url}{download_pbf_url}{filename}".format(
        pbf_path="data/osm/",
        download_server_url=regional_cfg["download_server_url"],
        download_pbf_url=regional_cfg["download_pbf_url"],
        filename=filename,
    ))


@task
def create_pgpass(default=False):
    pg_conn = Variable.get(key="conn_default", deserialize_json=True)
    atlas_region = "default"
    if not default:
        atlas_region = Variable.get(key="atlas_region").strip('\"')
        pg_conn = Variable.get(key=regional_config(atlas_region), deserialize_json=True)
    pgpass_file = "config/{atlas_region}.pgpass".format(atlas_region=atlas_region)
    f = open(pgpass_file, "w")
    f.write(db_pass(pg_conn["db_conn"]))
    f.close()
    run_shell_command("chmod 600 {pgpass_file}".format(pgpass_file=pgpass_file))


@task
def create_db():
    atlas_region = Variable.get(key="atlas_region").strip('\"')
    regional_cfg = Variable.get(key=regional_config(atlas_region), deserialize_json=True)
    regional_conn = regional_cfg["db_conn"]
    default_conn = Variable.get(key="conn_default", deserialize_json=True)["db_conn"]
    run_shell_command("dags/sql/commons/create_db.sh {default_pgpass} {db_pgpass} {user} \
                      {password} {schema} {default_host} {default_user} {default_schema}".format(
        default_pgpass="config/default.pgpass",
        db_pgpass="config/{atlas_region}.pgpass".format(
            atlas_region=atlas_region
        ),
        user=regional_conn["user"],
        password=regional_conn["password"],
        schema=regional_conn["schema"],
        default_host=default_conn["host"],
        default_user=default_conn["user"],
        default_schema=default_conn["schema"],
    ))
    add_conn(db_conn(regional_cfg["db_conn"]))


@task
def osm2pgsql():
    atlas_region = Variable.get(key="atlas_region").strip('\"')
    regional_cfg = Variable.get(key=regional_config(atlas_region), deserialize_json=True)
    regional_conn = regional_cfg["db_conn"]
    run_shell_command("dags/sql/import_osm/osm2pgsql.sh {db_pgpass} {pbf_path}{filename} \
                      {schema} {user} {host}".format(
        db_pgpass="config/{atlas_region}.pgpass".format(atlas_region=atlas_region),
        pbf_path="data/osm/",
        filename="{atlas_region}-latest.osm.pbf".format(atlas_region=atlas_region),
        schema=regional_conn["schema"],
        user=regional_conn["user"],
        host=regional_conn["host"],
    ))


with DAG(
    "import_osm",
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
    set_variable() >> \
    [create_pgpass(True), create_pgpass()] >> \
    create_db() >> \
    download_pbf() >> \
    osm2pgsql()
