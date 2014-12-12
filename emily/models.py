# coding: latin-1

import bcrypt
import json
import os
import psycopg2
import psycopg2.extras
import shortuuid
import urlparse
import uuid

from uuidencoder import UUIDEncoder as enc

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

    _add = "INSERT INTO users VALUES (%s, %s, %s);"
    _from_email = "SELECT * FROM users WHERE email=%s;"
    _from_uuid = "SELECT * FROM users WHERE uuid=%s;"

    def __init__(self, **kwargs):
        self.uuid = kwargs.get("uuid", uuid.uuid4())
        self.email = kwargs.get("email")


    def challenge(self, password):
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(User._from_uuid, (self.uuid,))
            u = cur.fetchone()
            if (bcrypt.hashpw(password, u["hashed_pass"]) == u["hashed_pass"]):
                return True
            else:
                return False


    def to_client(self):
        return json.dumps({"uuid": self.uuid}, separators=(",", ":"), cls=enc)


    @classmethod
    def from_email(cls, email):
        with con.cursor(cursor_factor=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(User._from_email, (email,))
            u = cur.fetchone()
            if u is None:
                return None
            else:
                return User(u)


    @classmethod
    def register_new(cls, email, password):
        if User.from_email(email) is None:
            u = User()
            hashed = bcrypt.hashpw(password, bcrypt.gensalt(15))
            with con.cursur() as cur:
                cur.execute(User._add, (u.uuid, email, h,))
                con.commit()
            return u
        else:
            return None


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
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(UserList._select % self.gatsby.table_name, (key,))
            return cur.fetchone()


    def __setitem__(self, key):
        self.add(key)


class Gatsby(B57Mixin):

    _table_prefix = "gatsby_users_"
    _select = "SELECT * FROM gatsbys WHERE uuid=%s"
    _register = "INSERT INTO gatsbys VALUES (%s, %s);"
    _unregister = "DELETE FROM gatsbys WHERE uuid=%s;"
    _create = "CREATE TABLE \"%s\" (uuid uuid, pending_card uuid, last_seen uu"\
            "id, last_seen_time timestamptz, CONSTRAINT \"%s_pKey\" PRIMARY KE"\
            "Y(id));"
    _drop = "DROP TABLE \"%s\";"

    def __init__(self, **kwargs):
        self._api = kwargs
        self.uuid = kwargs.get("uuid", uuid.uuid4())
        self.table_name = kwargs.get("table_name", self._new_table_name())
        self.users = UserList(self)


    def _new_table_name(self):
        return Gatsby._table_prefix + self.b57id()


    def destroy(self):
        with con.cursor() as cur:
            cur.execute(Gatsby._unregister, (self.uuid,))
            cur.execute(Gatsby._drop % self._api["table_name"])
            con.commit()


    @classmethod
    def new(cls):
        g = Gatsby()
        t = g._new_table_name()
        with con.cursor() as cur:
            cur.execute(Gatsby._create % (t, t))
            cur.execute(Gatsby._register, (g.uuid, t,))
            con.commit()
        return g


    @classmethod
    def from_uuid(cls, uid):
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(Gatsby._select, (uid,))
            return Gatsby(**cur.fetchone())


    @classmethod
    def from_b57id(cls, b57id):
        return Gatsby.from_uuid(shortuuid.decode(b57id))


class Card(B57Mixin):

    _from_id = "SELECT * FROM cards WHERE uuid=%s;"
    _from_rnd = "SELECT * FROM cards ORDER BY RANDOM() LIMIT 1;"

    def __init__(self, **kwargs):
        self._api = kwargs
        self.uuid = kwargs["uuid"]


    def api(self):
        return self._api


    @classmethod
    def from_uuid(cls, uid):
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(Card._from_id, (uid,))
            return Card(**cur.fetchone())


    @classmethod
    def from_b57id(cls, b57id):
        return Card.from_uuid(shortuuid.decode(b57id))


    @classmethod
    def at_random(cls):
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(Card._from_rnd)
            return Card(**cur.fetchone())
