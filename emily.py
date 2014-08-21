# coding: latin-1

import base64
import os
import psycopg2
import sheet
from flask import Flask

emily = Flask(__name__)


def load_environment(name):
    if name not in os.environ:
        raise RuntimeError("{n} not in environment".format(n=name))
    return os.environ[name]

# Load environment
heroku_api_key = load_environment("HEROKU_API_KEY")
emily_url = load_environment("EMILY_URL")
db_host = load_environment("DB_HOST")
db_port = load_environment("DB_PORT")
db_name = load_environment("DB_NAME")
db_user = load_environment("DB_USER")
db_password = load_environment("DB_PASSWORD")
gatsby_app_name = load_environment("GATSBY_APP_NAME")

# Configure connections
headers = {"Authorization": base64.b64encode(":" + heroku_api_key),
           "Accept": "application/vnd.heroku+json; version=3",
           "User-Agent": "Partier-Emily/0.0"}
heroku = sheet.Sheet("https://api.heroku.com", headers=headers)
db = psycopg2.connect(host=db_host, port=db_port, dbname=db_name, user=db_user,
                      password=db_password)

# Find Gatsby
apps = heroku.apps.GET().json()
gatsby_app = filter(lambda a: a["name"] == gatsby_app_name, apps)
if len(gatsby_app) == 0:
    raise RuntimeError("Cannot locate Gatsby app: {}".format(gatsby_app_name))
gatsby_app = gatsby_app[0]


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
    port = 80
    if "PORT" in os.environ:
        port = int(os.environ["PORT"])
    emily.run(debug=True, port=port, host="0.0.0.0")
