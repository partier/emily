# coding: latin-1

import json
import os
import psycopg2
import psycopg2.extras
import shortuuid
import urlparse
import uuid


def load_environment(name):
    if name not in os.environ:
        raise RuntimeError("{n} not in environment".format(n=name))
    return os.environ[name]


psycopg2.extras.register_uuid()
url = urlparse.urlparse(load_environment("DATABASE_URL"))
con = psycopg2.connect(
        database=url.path[1:], user=url.username, password=url.password,
        host=url.hostname, port=url.port)


class B57Mixin(object):

    def b57id(self):
        return shortuuid.encode(self.uuid)


class User(object):

    def __init__(self, **kwargs):
        self._api = kwargs
        self.uuid = kwargs.get("uuid", uuid.uuid4())


class UserList(object):

    ADD = "INSERT INTO \"%s\" VALUES (%%s);"
    REMOVE = "DELETE FROM \"%s\" WHERE uuid=%%s;"
    SELECT = "SELECT * FROM \"%s\" WHERE uuid=%%s;"

    def __init__(self, gatsby):
        self.gatsby = gatsby


    def add(self, uid):
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(UserList.ADD % self.gatsby.table_name, (uid,))
            con.commit()


    def remove(self, user):
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(UserList.REMOVE % self.gatsby.table_name, (user.uuid,))
            con.commit()


    def __getitem__(self, key):
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(UserList.SELECT % self.gatsby.table_name, (key,))
            return cur.fetchone()


    def __setitem__(self, key):
        self.add(key)


class Gatsby(B57Mixin):

    TABLE_PREFIX = "gatsby_users_"
    SELECT = "SELECT * FROM gatsbys WHERE uuid=%s"
    REGISTER = "INSERT INTO gatsbys VALUES (%s, %s);"
    UNREGISTER = "DELETE FROM gatsbys WHERE uuid=%s;"
    CREATE = "CREATE TABLE \"%s\" (uuid uuid, pending_card uuid, last_seen uuid,"\
             "last_seen_time timestamptz, CONSTRAINT \"%s_pKey\" PRIMARY KEY(i"\
             "d));"
    DROP = "DROP TABLE \"%s\";"

    def __init__(self, **kwargs):
        self._api = kwargs
        self.uuid = kwargs.get("uuid", uuid.uuid4())
        self.table_name = kwargs.get("table_name", self._new_table_name())
        self.users = UserList(self)


    def _new_table_name(self):
        return Gatsby.TABLE_PREFIX + self.b57id()


    def destroy(self):
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(Gatsby.UNREGISTER, (self.uuid,))
            cur.execute(Gatsby.DROP % self._api["table_name"])
            con.commit()


    @classmethod
    def new(cls):
        g = Gatsby()
        t = g._new_table_name()
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(Gatsby.CREATE % (t, t))
            cur.execute(Gatsby.REGISTER, (g.uuid, t,))
            con.commit()
        return g


    @classmethod
    def from_uuid(cls, uid):
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(Gatsby.SELECT, (uid,))
            return Gatsby(**cur.fetchone())


    @classmethod
    def from_b57id(cls, b57id):
        return Gatsby.from_uuid(shortuuid.decode(b57id))


class Card(B57Mixin):

    FROM_ID = "SELECT * FROM cards WHERE uuid=%s;"
    FROM_RND = "SELECT * FROM cards ORDER BY RANDOM() LIMIT 1;"

    def __init__(self, **kwargs):
        self._api = kwargs
        self.uuid = kwargs["uuid"]


    def api(self):
        return self._api


    @classmethod
    def from_uuid(cls, uid):
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(Card.FROM_ID, (uid,))
            return Card(**cur.fetchone())


    @classmethod
    def from_b57id(cls, b57id):
        return Card.from_uuid(shortuuid.decode(b57id))


    @classmethod
    def at_random(cls):
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(Card.FROM_RND)
            return Card(**cur.fetchone())
