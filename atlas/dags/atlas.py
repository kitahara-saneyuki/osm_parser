from __future__ import annotations

import logging

from datetime import datetime, timedelta
from textwrap import dedent

from airflow import DAG
from airflow.decorators import task
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from datetime import datetime

@task
def variable_set():
    Variable.set(key="updated_giftcard_id", value="0", serialize_json=True)
    Variable.set(
        key="last_ids", value={"updated_giftcard_id": "0", "updated_order_id": "1"}, serialize_json=True
    )

@task
def variable_get():
    logging.info(Variable.get(key="updated_giftcard_id", deserialize_json=True))
    logging.info(Variable.get(key="last_ids", deserialize_json=True))

with DAG(
    "atlas",
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
    variable_set() >> variable_get()
