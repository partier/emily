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

@emily.route("/card", methods=["GET"])
def card():
    card = db.random_card()
    return redirect(
        url_for("card_from_id", b57id=shortuuid.encode(card["id"])))


@emily.route("/card/<b57id>", methods=["GET"])
def card_from_id(b57id):
    card = db.card_from_id(shortuuid.decode(b57id))
    return json.dumps(card, separators=(",", ":"), cls=encoder)


@emily.route("/gatsby", methods=["POST"])
def gatsby():
    try:
        g_uuid = uuid.uuid4()
        g_b57id = shortuuid.encode(g_uuid)
        table = "gatsby_users_" + str(g_uuid)
        db.create_gatsby_table(table)
        db.register_gatsby_table(g_uuid, table)
        return ("WAT", 201, {"Location": url_for("gatsby_from_id", b57id=g_b57id)})
    except Exception as e:
        print e


@emily.route("/gatsby/<b57id>", methods=["DELETE"])
def gatsby_from_id(b57id):
    g_uuid = shortuuid.decode(b57id)
    table = "gatsby_users_" + str(g_uuid)
    db.drop_gatsby_table(table)
    db.unregister_gatsby_table(g_uuid)


@emily.route("/", methods=["GET"])
def main():
    return ("Manners are a sensitive awareness of the feelings of others. If y"
            "ou have that awareness, you have good manners, no matter what for"
            "k you use.")


if __name__ == "__main__":
    emily.run(debug=True, port=int(os.environ["PORT"]), host="0.0.0.0")
