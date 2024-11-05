from flask import Flask
import os

app = Flask(__name__)
app.secret_key = os.urandom(32)

from .routes import *

if __name__ == "__main__":
    app.debug = True
    app.run()