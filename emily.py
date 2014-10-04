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


@emily.route("/redirect")
def redirect_test():
    card = db.random_card()
    return redirect(
        url_for("card_from_id", b57id=shortuuid.encode(card["id"])))


@emily.route("/")
def main():
    return ("Manners are a sensitive awareness of the feelings of others. If y"
            "ou have that awareness, you have good manners, no matter what for"
            "k you use.")

if __name__ == "__main__":
    emily.run(debug=True, port=int(os.environ["PORT"]), host="0.0.0.0")
