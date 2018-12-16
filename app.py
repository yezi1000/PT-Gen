# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>

from flask import Flask
from flask_cors import CORS
from flask_caching import Cache

app = Flask(__name__)


cache = Cache(app)

CORS(app)
