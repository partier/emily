# coding: latin-1

import bcrypt
import inspect
import json
import os
import psycopg2
import psycopg2.extras
import shortuuid
import sys
import urlparse
import uuid

from uuidencoder import UUIDEncoder as enc
from psycopg2.extras import RealDictCursor as dict_cursor

def load_environment(name):
    if name not in os.environ:
        raise RuntimeError("{n} not in environment".format(n=name))
    return os.environ[name]


psycopg2.extras.register_uuid()
url = load_environment("DATABASE_URL")
db = urlparse.urlparse(url)
psql_args = {"database": db.path[1:],
             "user": db.username,
             "host": db.hostname,
             "port": db.port,
             "password": db.password}
print("Connecting to Postgres from URL:\nURL: {}\n{}".format(url, psql_args))
con = psycopg2.connect(**psql_args)


def create_tables():
    for _, obj in inspect.getmembers(sys.modules[__name__]):
        if (inspect.isclass(obj) and issubclass(obj, TableMixin) and
                (obj is not TableMixin)):
            if not obj.table_exists():
                obj.table_create()


class B57Mixin(object):

    def b57id(self):
        return shortuuid.encode(self.uuid)


class TableMixin(object):

    _create = "CREATE TABLE {} ({});"
    _exists = "SELECT table_name FROM information_schema.tables WHERE table_na"\
              "me=%s;"

    @classmethod
    def table_create(cls):
        schema = ""
        for col in cls._table_schema:
            schema += col[0] + " " + col[1] + ","
        schema = schema[:-1]
        with con.cursor() as cur:
            cur.execute(TableMixin._create.format(cls._table_name, schema))
            con.commit()

    @classmethod
    def table_exists(cls):
        exists = False
        with con.cursor() as cur:
            cur.execute(TableMixin._exists, (cls._table_name,))
            if cur.rowcount > 0:
                exists = True
        return exists


class User(TableMixin):

    _table_name = "users"
    _table_schema = [("uuid", "uuid"),
                     ("email_addr", "character varying"),
                     ("hashed_pass", "character varying")]
    _add = "INSERT INTO {} VALUES (%s, %s, %s);".format(_table_name)
    _from_email = "SELECT * FROM {} WHERE email_addr=%s;".format(_table_name)
    _from_uuid = "SELECT * FROM {} WHERE uuid=%s;".format(_table_name)

    def __init__(self, **kwargs):
        self.uuid = kwargs.get("uuid", uuid.uuid4())
        self.email = kwargs.get("email")


    def challenge(self, password):
        with con.cursor(cursor_factory=dict_cursor) as cur:
            cur.execute(User._from_uuid, (self.uuid,))
            u = cur.fetchone()
            con.commit()
            if (bcrypt.hashpw(password, u["hashed_pass"]) == u["hashed_pass"]):
                return True
            else:
                return False


    def to_client(self):
        return json.dumps({"uuid": self.uuid}, separators=(",", ":"), cls=enc)


    @classmethod
    def from_email(cls, email):
        u = None
        with con.cursor(cursor_factory=dict_cursor) as cur:
            cur.execute(cls._from_email, (email,))
            con.commit() # Without, this query will hang indefinitely. Why?
            u = cur.fetchone()
        if u is None:
            return None
        else:
            return User(**u)


    @classmethod
    def register_new(cls, email, password):
        u = cls.from_email(email)
        if u is None:
            u = User(email=email)
            hashed = bcrypt.hashpw(password, bcrypt.gensalt(15))
            with con.cursor() as cur:
                cur.execute(User._add, (u.uuid, email, hashed,))
                con.commit()
        else:
            if not u.challenge(password):
                u = None
        return u


class UserList(object):

    _add = "INSERT INTO \"%s\" VALUES (%%s);"
    _remove = "DELETE FROM \"%s\" WHERE uuid=%%s;"
    _select = "SELECT * FROM \"%s\" WHERE uuid=%%s;"

    def __init__(self, gatsby):
        self.gatsby = gatsby


    def add(self, uid):
        with con.cursor() as cur:
            cur.execute(UserList._add % self.gatsby.table_name, (uid,))
            con.commit()


    def remove(self, user):
        with con.cursor() as cur:
            cur.execute(UserList._remove % self.gatsby.table_name, (user.uuid,))
            con.commit()


    def __getitem__(self, key):
        with con.cursor(cursor_factory=dict_cursor) as cur:
            cur.execute(UserList._select % self.gatsby.table_name, (key,))
            return cur.fetchone()


    def __setitem__(self, key):
        self.add(key)


class Gatsby(B57Mixin, TableMixin):

    _table_name = "gatsbys"
    _table_schema = [("uuid", "uuid"),
                     ("table_name", "character varying")]
    _prefix = "gatsby_users_"
    _select = "SELECT * FROM {} WHERE uuid=%s".format(_table_name)
    _register = "INSERT INTO {} VALUES (%s, %s);".format(_table_name)
    _unregister = "DELETE FROM {} WHERE uuid=%s;".format(_table_name)
    _create = "CREATE TABLE \"%s\" (user uuid, pending_card uuid, last_seen uu"\
            "id, last_seen_time timestamptz, CONSTRAINT \"%s_pKey\" PRIMARY KE"\
            "Y(user));"
    _drop = "DROP TABLE \"%s\";"

    def __init__(self, **kwargs):
        self._api = kwargs
        self.uuid = kwargs.get("uuid", uuid.uuid4())
        self.table_name = kwargs.get("table_name", self._new_table_name())
        self.users = UserList(self)


    def _new_table_name(self):
        return Gatsby._prefix + self.b57id()


    def destroy(self):
        with con.cursor() as cur:
            cur.execute(Gatsby._unregister, (self.uuid,))
            cur.execute(Gatsby._drop % self._api["table_name"])
            con.commit()


    @classmethod
    def new(cls):
        g = cls()
        t = g._new_table_name()
        with con.cursor() as cur:
            cur.execute(cls._create % (t, t))
            cur.execute(cls._register, (g.uuid, t,))
            con.commit()
        return g


    @classmethod
    def from_uuid(cls, uid):
        with con.cursor(cursor_factory=dict_cursor) as cur:
            cur.execute(cls._select, (uid,))
            return Gatsby(**cur.fetchone())


    @classmethod
    def from_b57id(cls, b57id):
        return cls.from_uuid(shortuuid.decode(b57id))


class Card(B57Mixin, TableMixin):

    _table_name = "cards"
    _table_schema = [("uuid", "uuid"),
                     ("title", "character varying"),
                     ("body", "character varying"),
                     ("help", "character varying"),
                     ("type", "character varying")]
    _from_id = "SELECT * FROM cards WHERE uuid=%s;"
    _from_rnd = "SELECT * FROM cards ORDER BY RANDOM() LIMIT 1;"

    def __init__(self, **kwargs):
        self._api = kwargs
        self.uuid = kwargs["uuid"]


    def api(self):
        return self._api


    @classmethod
    def from_uuid(cls, uid):
        with con.cursor(cursor_factory=dict_cursor) as cur:
            cur.execute(cls._from_id, (uid,))
            return cls(**cur.fetchone())


    @classmethod
    def from_b57id(cls, b57id):
        return cls.from_uuid(shortuuid.decode(b57id))


    @classmethod
    def at_random(cls):
        with con.cursor(cursor_factory=dict_cursor) as cur:
            cur.execute(cls._from_rnd)
            con.commit()
            return cls(**cur.fetchone())
