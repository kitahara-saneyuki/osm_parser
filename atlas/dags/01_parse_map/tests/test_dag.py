import json
import logging
import time

from airflow.models import DagBag
from airflow.api.client.local_client import Client

from datetime import datetime

from utils.db import PGConn


def test_dagbag():
    dag_bag = DagBag(include_examples=False)
    dag_bag.process_file("01a_download_pbf.py")
    dag_bag.process_file("01a_set_test_vars.py")
    dag_bag.process_file("01b_import_osm.py")
    dag_bag.process_file("01c_parse_osm.py")
    dag_bag.process_file("01d_assign_maxspeed.py")
    assert len(dag_bag.import_errors) == 0


def test_import_osm():
    # Trigger DAGs
    c = Client(None, None)
    logging.info("----- Testing import OSM -----")
    c.trigger_dag(
        dag_id="01a_set_test_vars",
        conf={"atlas_region": "bristol"},
        execution_date=datetime.now().astimezone(),
    )
    time.sleep(60)

    # Verifying data
    logging.info("----- Verifying OSM data -----")
    regional_cfg = json.load(open("./config/regions/bristol.json"))
    data_verify_road = regional_cfg["data_verify"]["road"]
    pg_conn = PGConn(regional_cfg["db_conn"])
    pg_res = {
        row["highway"]: row["count"]
        for row in pg_conn.run_query(
            "SELECT highway, count(*) FROM osm_edges group by highway;"
        )
    }
    for highway, count in data_verify_road.items():
        assert highway in pg_res
        assert count == pg_res[highway]
