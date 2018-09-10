from flask import Flask, make_response
from flask_restful import Api

app = Flask(__name__)
api = Api(app)

from .core import app_setup


if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=True, port=80)
