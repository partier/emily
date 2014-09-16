# coding: latin-1

import base64
import os
import psycopg2
import urlparse
import sheet
import json
from flask import Flask

emily = Flask(__name__)


def load_environment(name):
    if name not in os.environ:
        raise RuntimeError("{n} not in environment".format(n=name))
    return os.environ[name]

# Load environment
heroku_api_key = load_environment("HEROKU_API_KEY")
emily_url = load_environment("EMILY_URL")
db_url = urlparse.urlparse(load_environment("DATABASE_URL"))

# Configure connections
headers = {"Authorization": base64.b64encode(":" + heroku_api_key),
           "Accept": "application/vnd.heroku+json; version=3",
           "User-Agent": "Partier-Emily/0.0"}
heroku = sheet.Sheet("https://api.heroku.com", headers=headers)
db = psycopg2.connect(
        database=db_url.path[1:],
        user=db_url.username,
        password=db_url.password,
        host=db_url.hostname,
        port=db_url.port)


@emily.route("/card")
def card():
    # Test card:
    card = { "title": "Best card title EVER",
             "body": "Some lorum ipsum nonsense",
             "help": "Flavor text. Something witty",
             "type": "Test card type"}
    return json.dumps(card)


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

if __name__ == "__main__":
    emily.run(debug=True, port=int(os.environ["PORT"]), host="0.0.0.0")
