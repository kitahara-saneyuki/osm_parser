import shlex
import logging
import subprocess

from io import StringIO

from airflow import settings
from airflow.models.connection import Connection

from sqlalchemy import exc


def run_shell_command(command_line):
    command_line_args = shlex.split(command_line)
    logging.info('Subprocess: "' + command_line + '"')
    try:
        command_line_process = subprocess.Popen(
            command_line_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        process_output, _ =  command_line_process.communicate()
        for line in process_output.decode("utf-8").split("\n"):
            logging.info(line)
        process_output = StringIO(process_output.decode("utf-8"))
    except Exception as exc:
        logging.info('Exception occurred: ' + str(exc))
        logging.info('Subprocess failed')
        return False
    else:
        # no exception was raised
        logging.info('Subprocess finished')
    return True


def regional_config(atlas_region):
    return "regional_config_{atlas_region}".format(
        atlas_region=atlas_region
    )


def db_conn(conn):
    return Connection(
        conn_id=conn["id"],
        conn_type=conn["type"],
        schema=conn["schema"],
        host=conn["host"],
        login=conn["user"],
        password=conn["password"],
        port=5432
    )


def db_pass(conn):
    return "{host}:{port}:{schema}:{username}:{password}".format(
        host=conn["host"],
        schema=conn["schema"],
        username=conn["user"],
        password=conn["password"],
        port=5432
    )


def add_conn(conn):
    session = settings.Session()
    try:
        session.add(conn)
        session.commit()
    except exc.IntegrityError as e:
        session.rollback()
