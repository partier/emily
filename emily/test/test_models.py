# coding: latin-1

import inspect
import os
import psycopg2
import sys
import urlparse
from nose.tools import ok_

# Bring module path into system, fix environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
db_url = "postgres://emily:password@localhost:5432/emily_test"
os.environ["DATABASE_URL"] = db_url

import models


con = None


def setup_module():
    global con
    url = urlparse.urlparse(os.environ["DATABASE_URL"])
    con = psycopg2.connect(
            database=url.path[1:], user=url.username, password=url.password,
            host=url.hostname, port=url.port)


class TestTableMixin(object):

    def test_table_create(self):
        for _, obj in inspect.getmembers(models):
            if (inspect.isclass(obj) and
                    issubclass(obj, models.TableMixin) and
                    (obj is not models.TableMixin)):
                yield self.table_create, obj
    
    def test_table_exists(self):
        for _, obj in inspect.getmembers(models):
            if (inspect.isclass(obj) and
                    issubclass(obj, models.TableMixin) and
                    (obj is not models.TableMixin)):
                yield self.table_exists, obj

    def test_table_not_exists(self):
        for _, obj in inspect.getmembers(models):
            if (inspect.isclass(obj) and
                    issubclass(obj, models.TableMixin) and
                    (obj is not models.TableMixin)):
                yield self.table_not_exists, obj

    def table_create(self, cls):
        cls.table_create()
        with con.cursor() as cur:
            select_table = "SELECT table_name FROM information_schema.tables W"\
                           "HERE table_name='{}';"
            cur.execute(select_table.format(cls._table_name))
            assert cur.rowcount > 0, "Failed to create table"
            select_cols = "SELECT column_name, data_type FROM information_sche"\
                          "ma.columns WHERE table_name='{}';"
            cur.execute(select_cols.format(cls._table_name))
            assert cur.rowcount > 0, "No columns in table"
            cols = cur.fetchall()
            cur.execute("DROP TABLE {};".format(cls._table_name))
            con.commit()
            missing = [c for c in cls._table_schema if c not in cols]
            if len(missing) > 0:
                raise Exception('Missing columns in table: {}'.format(missing))

    def table_exists(self, cls):
        cls.table_create()
        assert cls.table_exists(), "Can't verify created table exists"
        with con.cursor() as cur:
            cur.execute("DROP TABLE {};".format(cls._table_name))
            con.commit()

    def table_not_exists(self, cls):
        assert not cls.table_exists(), "False positive for table existing"