# coding: latin-1

import base64
import json
import os
import shortuuid
import uuid
from flask import Flask, redirect, request, url_for
from models import Card, Gatsby
from uuidencoder import UUIDEncoder as encoder

emily = Flask(__name__)


def force_ssl(fn):
    @wraps(fn)
    def check_ssl(*args, **kwargs):
        if request.is_secure:
            return fn(*args, **kwargs)
        else:
            return redirect(request.url.replace("http://", "https://"))
    return check_ssl


@force_ssl
@emily.route("/user", methods=["POST"])
def user():
    if "email" in request.json and "pass" in request.json:
        u = User.register_new(request.json["email"], request.json["password"])
        if u is not None:
            return (u.json(), 200, None)
    else:
        return (None, 400, None)


@emily.route("/card", methods=["GET"])
def card():
    c = Card.at_random()
    return redirect(
        url_for("card_from_id", b57id=c.b57id()))


@emily.route("/card/<b57id>", methods=["GET"])
def card_from_id(b57id):
    c = Card.from_b57id(b57id)
    return json.dumps(c.api(), separators=(",", ":"), cls=encoder)


@emily.route("/gatsby", methods=["POST"])
def gatsby():
    g = Gatsby.new()
    # TODO: Fire off Gatsby worker
    return (None, 201, {"Location": url_for("gatsby_from_id", b57id=g.b57id())})


@emily.route("/gatsby/<b57id>", methods=["DELETE"])
def gatsby_from_id(b57id):
    if request.method == "DELETE":
        Gatsby.from_b57id(b57id).destroy()


@emily.route("/", methods=["GET"])
def main():
    return ("Manners are a sensitive awareness of the feelings of others. If y"
            "ou have that awareness, you have good manners, no matter what for"
            "k you use.")


if __name__ == "__main__":
    emily.run(debug=True, port=int(os.environ["PORT"]), host="0.0.0.0")