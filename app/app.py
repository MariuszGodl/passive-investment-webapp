from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Sam init, nic ciekawego :p</p>"
