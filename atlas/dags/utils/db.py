import logging
import psycopg2

from airflow import settings
from airflow.models.connection import Connection
from airflow.providers.postgres.operators.postgres import PostgresOperator as _PostgresOperator

from sqlalchemy import exc
from psycopg2.extras import RealDictCursor


class PostgresOperator(_PostgresOperator):
    template_fields = [*_PostgresOperator.template_fields, "conn_id"]


def db_conn(conn):
    return Connection(
        conn_id=conn["id"],
        conn_type=conn["type"],
        schema=conn["schema"],
        host=conn["host"],
        login=conn["user"],
        password=conn["password"],
        port=5432,
    )


def db_pass(conn):
    return "{host}:{port}:{schema}:{username}:{password}".format(
        host=conn["host"],
        schema=conn["schema"],
        username=conn["user"],
        password=conn["password"],
        port=5432,
    )


def add_conn(conn):
    session = settings.Session()
    try:
        session.add(conn)
        session.commit()
    except exc.IntegrityError:
        session.rollback()


class PGConn:
    def __init__(self, conn_json):
        self.conn_json = conn_json

    def conn_pgsql(self):
        conn = psycopg2.connect(
            dbname=self.conn_json["schema"],
            user=self.conn_json["user"],
            password=self.conn_json["password"],
            host=self.conn_json["host"],
            port=self.conn_json["port"],
        )
        return conn

    def run_query(self, query):
        try:
            conn = self.conn_pgsql()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query)
            cursor_dump = cur.fetchall()
            conn.close()
            return cursor_dump
        except psycopg2.Error as e:
            logging.error(e.pgerror)
            logging.error(e.diag.message_detail)

    def run_query_map(self, query, id_col, table, id_arr):
        return {
            row[id_col]: (float(row["latitude"]), float(row["longitude"]))
            for row in self.run_query(
                query.format(id_col=id_col, table=table, id_arr=str(id_arr))
            )
        }
