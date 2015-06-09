# coding: latin-1

import bcrypt
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

user_uuid = "c7f35859-f0ef-4e2a-adc9-454c4f11c195"
user_email = "user@domain.tld"
user_passw = "password"
user_hash = bcrypt.hashpw(user_passw, bcrypt.gensalt())

basic_header = {"Content-Type": "application/json",
                "Accept": "application/json;"}

con = None

def setup_module():
    global con
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
        insert_user = "INSERT INTO {} VALUES (%s, %s, %s)"
        insert_user = insert_user.format(models.User._table_name)
        cur.execute(insert_user, (user_uuid, user_email, user_hash,))
        con.commit()


def teardown_module():
    con.close()


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


    def test_card_get_redirect(self):
        card_response = self.app.get("/card", follow_redirects=True)
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


    def test_user_post(self):
        email = "fake@email.com"
        passw = "1234"
        data = json.dumps({"email": email, "password": passw})
        response = self.app.post("/user", data=data, headers=basic_header)
        assert response.status_code == 200, "Should create user"
        data = json.loads(response.data)
        assert data["email"] == email, "Should match existing email"
        user = None
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            select = "SELECT * FROM {} WHERE email_addr=%s"
            select = select.format(models.User._table_name)
            cur.execute(select, (email,))
            assert cur.rowcount == 1, "Should have exactly one row"
            user = cur.fetchone()
            con.commit()
        c = bcrypt.hashpw(passw, user["hashed_pass"]) == user["hashed_pass"]
        assert c, "Should match hashed password" 


    def test_user_post_exists(self):
        data = json.dumps({"email": user_email, "password": user_passw})
        response = self.app.post("/user", data=data, headers=basic_header)
        assert response.status_code == 200, "Should locate user"
        data = json.loads(response.data)
        assert data["email"] == user_email, "Should match email"
        assert data["uuid"] == user_uuid, "Should match UUID"


    def test_user_post_invalid(self):
        data = json.dumps({"key": "some value"})
        response = self.app.post("/user", data=data, headers=basic_header)
        assert response.status_code == 400, "Should be bad request"
