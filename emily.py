# coding: latin-1

import os
from flask import Flask, request

emily = Flask(__name__)

if "HEROKU_API_KEY" not in os.environ:
    raise RuntimeError("No API key specified in environment")
heroku_api_key = os.environ["HEROKU_API_KEY"]


@emily.route("/new_game")
def new_game():
    return None


@emily.route("/close_game")
def close_game():
    return None


@emily.route("/")
def main():
    return ("Manners are a sensitive awareness of the feelings of others. If y"
            "ou have that awareness, you have good manners, no matter what for"
            "k you use.")


@emily.route("/shutdown")
def shutdown():
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the werkzeug server")
    func()
    return "Server shutting down..."

if __name__ == "__main__":
    port = 80
    if "PORT" in os.environ:
        port = int(os.environ["PORT"])
    emily.run(debug=True, port=port, host="0.0.0.0")
