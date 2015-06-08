# coding: latin-1

import json
import os
import psycopg2
import psycopg2.extras
import shortuuid
import sys
import tempfile
import urlparse
import uuid

# Bring module path into system, fix environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
db_url = "postgres://emily:password@localhost:5432/emily_test"
os.environ["DATABASE_URL"] = db_url

import emily.emily
import models

card_uuid = "c7f35859-f0ef-4e2a-adc9-454c4f11c196"
card_title = "Example Card Title"
card_body = "Example card bodies are the wordiest."
card_help = "Example card help: Maybe try harder."
card_type = "Example Card Type"


def setup_module():
    psycopg2.extras.register_uuid()
    url = urlparse.urlparse(os.environ["DATABASE_URL"])
    con = psycopg2.connect(
            database=url.path[1:], user=url.username, password=url.password,
            host=url.hostname, port=url.port)
    models.create_tables()
    with con.cursor() as cur:
        insert_card = "INSERT INTO {} VALUES (%s, %s, %s, %s, %s)"
        insert_card = insert_card.format(models.Card._table_name)
        cur.execute(insert_card, (card_uuid, card_title, card_body, card_help,
                                  card_type,))
        con.commit()


class TestEmily(object):

    def setUp(self):
        emily.emily.app.config["TESTING"] = True
        self.app = emily.emily.app.test_client()


    def test_card_get(self):
        redir = self.app.get("/card")
        assert redir.status_code == 302, "Should present redirect"
        location = redir.headers["Location"].split('/')[-1]
        card_response = self.app.get("/card/" + location)
        assert card_response.status_code == 200, "Card should be located"
        card = json.loads(card_response.get_data())
        keys = [k in card for k in zip(*models.Card._table_schema)[0]]
        assert all(keys), "Should contain all schema keys"


    def test_card_b57id_get(self):
        b57 = shortuuid.encode(uuid.UUID(card_uuid))
        card_response = self.app.get("/card/" + b57)
        assert card_response.status_code == 200, "Card should be located"
        card = json.loads(card_response.get_data())
        keys = [k in card for k in zip(*models.Card._table_schema)[0]]
        assert all(keys), "Should contain all schema keys"
