# coding: latin-1

import bcrypt
import inspect
import json
import os
import psycopg2
import psycopg2.extras
import sys
import urlparse
import uuid
from nose.tools import raises

# Bring module path into system, fix environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
db_url = "postgres://emily:password@localhost:5432/emily_test"
os.environ["DATABASE_URL"] = db_url

import models
from uuidencoder import UUIDEncoder as enc


con = None


def setup_module():
    global con
    psycopg2.extras.register_uuid()
    url = urlparse.urlparse(os.environ["DATABASE_URL"])
    con = psycopg2.connect(
            database=url.path[1:], user=url.username, password=url.password,
            host=url.hostname, port=url.port)
    for _, obj in inspect.getmembers(models):
        if (inspect.isclass(obj) and
                issubclass(obj, models.TableMixin) and
                (obj is not models.TableMixin)):
            with con.cursor() as cur:
                select_table = "SELECT table_name FROM information_schema.tabl"\
                               "es WHERE table_name=%s"
                cur.execute(select_table, (obj._table_name,))
                if cur.rowcount > 0:
                    cur.execute("DROP TABLE {};".format(obj._table_name))
                    con.commit()


def teardown_module():
    con.close()


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



class TestUser(object):

    @classmethod
    def setup_class(cls):
        models.User.table_create()
        with con.cursor() as cur:
            insert = "INSERT INTO {} VALUES (%s, %s, %s)"
            pword = bcrypt.hashpw("password", bcrypt.gensalt())
            args = (uuid.uuid4(), "email@test.com", pword)
            cur.execute(insert.format(models.User._table_name), args)
            con.commit()


    @classmethod
    def teardown_class(cls):
        with con.cursor() as cur:
            cur.execute("DROP TABLE {};".format(models.User._table_name))
            con.commit()


    def test_init_excess_dict(self):
        u = models.User(**{"email": "something", "extra": "yes"})
        assert not hasattr(u, "extra"), "Should not have erroneous attribute"


    def test_init_missing_uuid(self):
        u = models.User(**{"email": "what"})
        assert u.uuid is not None, "Should create deault UUID"


    def test_init_missing_email(self):
        u = models.User()
        assert u.email is None, "Should not error on absent init vars"


    def test_to_client(self):
        u = models.User()
        out = u.to_client()
        assert type(out) is str, "Should return string (json)"
        load = json.loads(out)
        assert type(load) is dict, "Should load output as dictionary"
        assert "uuid" in load, "Should have 'uuid' key in output"


    def test_from_email(self):
        u = models.User.from_email("email@test.com")
        assert u is not None, "Should find known users from valid email"


    def test_from_email_none(self):
        u = models.User.from_email(None)
        assert u is None, "Should not have found user from None email"


    def test_from_email_blank(self):
        u = models.User.from_email("")
        assert u is None, "Should not have found user from blank email"


    def test_register_new(self):
        email = "new@user.net"
        passw = "1234"
        u = models.User.register_new(email, passw)
        assert hasattr(u, "uuid"), "Should have uuid attr"
        assert hasattr(u, "email"), "Should have email attr"
        assert type(u.uuid) is uuid.UUID, "Should be type UUID"
        assert u.email is not None, "Should have value"
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            select = "SELECT * FROM {} WHERE uuid=%s"
            select = select.format(models.User._table_name)
            cur.execute(select, (u.uuid,))
            assert cur.rowcount == 1, "Should have exactly one result"
            result = cur.fetchone()
            assert result["email_addr"] == email, "Should match register email"
            hp = result["hashed_pass"]
            assert bcrypt.hashpw(passw, hp) == hp, "Should verify password"


    def test_register_new_existing(self):
        email = "email@test.com"
        passw = "password"
        uid = None
        with con.cursor(cursor_factory = psycopg2.extras.RealDictCursor) as cur:
            select = "SELECT * FROM {} WHERE email_addr=%s"
            select = select.format(models.User._table_name)
            cur.execute(select, (email,))
            uid = cur.fetchone()["uuid"]
            con.commit()
        u = models.User.register_new(email, passw)
        assert u.uuid == uid, "Should match exiting UUID"
