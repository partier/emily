# coding: latin-1

import os
import psycopg2
import psycopg2.extras
import urlparse


def load_environment(name):
    if name not in os.environ:
        raise RuntimeError("{n} not in environment".format(n=name))
    return os.environ[name]


psycopg2.extras.register_uuid()
db_url = urlparse.urlparse(load_environment("DATABASE_URL"))
db_con = psycopg2.connect(
        database=db_url.path[1:],
        user=db_url.username,
        password=db_url.password,
        host=db_url.hostname,
        port=db_url.port)


def random_card():
    cur = db_con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM cards ORDER BY RANDOM() LIMIT 1;")
    return cur.fetchone()


def card_from_id(card_id):
    cur = db_con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM cards WHERE id=%s;", (card_id,))
    return cur.fetchone()