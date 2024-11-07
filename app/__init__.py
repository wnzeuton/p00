# Will Nzeuton, Tim Ng, Daniel Park, Yinwei Zhang
# Team lobo
# SoftDev
# p00 -- scenario 2
# 2024-11-07
from flask import Flask
import os

app = Flask(__name__)
app.secret_key = os.urandom(32)

from .blog_routes import *
from .util_routes import *

if __name__ == "__main__":
    app.debug = True
    app.run()
