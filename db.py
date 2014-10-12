# coding: latin-1

import os
import psycopg2
import psycopg2.extras
import urlparse


def load_environment(name):
    if name not in os.environ:
        raise RuntimeError("{n} not in environment".format(n=name))
    return os.environ[name]

SELECT_CARD_RND = "SELECT * FROM cards ORDER BY RANDOM() LIMIT 1;"
SELECT_CARD_ID = "SELECT * FROM cards WHERE id=%s;"
REGISTER_GATSBY = "INSERT INTO gatsbys VALUES (%s, %s);"
UNREGISTER_GATSBY = "DELETE FROM gatsbys WHERE id=%s;"
CREATE_GATSBY = "CREATE TABLE \"%s\" (id uuid, pending_card uuid, last_seen uu"\
                "id, last_seen_time timestamptz, heartbeat timestamptz, CONSTR"\
                "AINT \"%s_pKey\" PRIMARY KEY(id));"
DROP_GATSBY = "DROP TABLE \"%s\";"


psycopg2.extras.register_uuid()
db_url = urlparse.urlparse(load_environment("DATABASE_URL"))
db_con = psycopg2.connect(
        database=db_url.path[1:],
        user=db_url.username,
        password=db_url.password,
        host=db_url.hostname,
        port=db_url.port)

    
def random_card():
    with db_con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(SELECT_CARD_RND)
        return cur.fetchone()


def card_from_id(card_id):
    with db_con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(SELECT_CARD_ID, (card_id,))
        return cur.fetchone()


def create_gatsby_table(table_name):
    query = CREATE_GATSBY % (table_name, table_name)
    with db_con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query)
        db_con.commit()


def register_gatsby_table(g_uuid, table_name):
    with db_con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur = db_con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(REGISTER_GATSBY, (g_uuid, table_name,))
        db_con.commit()


def drop_gatsby_table(table_name):
    query = DROP_GATSBY % table_name
    with db_con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(DROP_GATSBY)
        db_con.commit()


def unregister_gatsby_table(g_uuid):
    with db_con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(UNREGISTER_GATSBY, (g_uuid,))
        db_con.commit()
