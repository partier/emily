# coding: latin-1

import os
import heroku
import psycopg2
from flask import Flask, request

emily = Flask(__name__)


def load_environment(name):
    if name not in os.environ:
        raise RuntimeError("{n} not in environment".format(n=name))
    return os.environ[name]

heroku_api_key = load_environment("HEROKU_API_KEY")
emily_url = load_environment("EMILY_URL")
db_host = load_environment("DB_HOST")
db_port = load_environment("DB_PORT")
db_name = load_environment("DB_NAME")
db_user = load_environment("DB_USER")
db_password = load_environment("DB_PASSWORD")
gatsby_app_name = load_environment("GATSBY_APP_NAME")

db = psycopg2.connect(host=db_host, port=db_port, dbname=db_name, user=db_user,
                      password=db_password)

platform = heroku.from_key(heroku_api_key)

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
