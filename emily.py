# coding: latin-1

import base64
import db
import json
import os
import uuid
from flask import Flask
from uuidencoder import UUIDCapableEncoder as encoder

emily = Flask(__name__)

@emily.route("/card")
def card():
    return json.dumps(db.random_card(), separators=(",", ":"), cls=encoder)


@emily.route("/card/<b64id>")
def card_from_id(b64id):
    card_id = uuid.UUID(bytes=base64.urlsafe_b64decode(b64id.encode("ascii")))
    card = db.card_from_id(card_id)
    print card
    return json.dumps(card, separators=(",", ":"), cls=encoder)


@emily.route("/")
def main():
    return ("Manners are a sensitive awareness of the feelings of others. If y"
            "ou have that awareness, you have good manners, no matter what for"
            "k you use.")

if __name__ == "__main__":
    emily.run(debug=True, port=int(os.environ["PORT"]), host="0.0.0.0")
