# coding: latin-1

import base64
import db
import json
import os
import shortuuid
import uuid
from flask import Flask, redirect, url_for
from uuidencoder import UUIDCapableEncoder as encoder

emily = Flask(__name__)

@emily.route("/card")
def card():
    return json.dumps(db.random_card(), separators=(",", ":"), cls=encoder)


@emily.route("/card/<b57id>")
def card_from_id(b57id):
    card = db.card_from_id(shortuuid.decode(b57id))
    return json.dumps(card, separators=(",", ":"), cls=encoder)


@emily.route("/gatsby", methods=["GET"])
def gatsby():
    g_uuid = uuid.uuid4()
    g_b57id = shortuuid.encode(g_uuid)
    db.create_gatsby_table("gatsby_users_" + g_b57id)
    db.register_gatsby_table(g_uuid, g_b57id)
    return None, 201, {"Location": url_for("gatsby_from_id", b57id=g_b57id)}
    

@emily.route("/gatsby/<b57id>", methods=["GET"])
def gatsby_from_id(b57id):
    return None


@emily.route("/", methods=["GET"])
def main():
    return ("Manners are a sensitive awareness of the feelings of others. If y"
            "ou have that awareness, you have good manners, no matter what for"
            "k you use.")


if __name__ == "__main__":
    emily.run(debug=True, port=int(os.environ["PORT"]), host="0.0.0.0")
