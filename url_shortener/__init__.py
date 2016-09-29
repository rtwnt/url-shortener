# -*- coding: utf-8 -*-
"""
url-shortener
==============

An application for generating and storing shorter aliases for
requested URLs. Uses `spam-lists`__ to prevent generating a short URL
for an address recognized as spam, or to warn a user a pre-existing
short alias has a target that has been later recognized as spam.

.. __: https://github.com/piotr-rusin/spam-lists
"""

__title__ = 'url-shortener'
__version__ = '0.9.0.dev1'
__author__ = 'Piotr Rusin'
__email__ = "piotr.rusin88@gmail.com"
__license__ = 'MIT'
__copyright__ = 'Copyright 2016 Piotr Rusin'

from blinker import Namespace
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

url_shortener_signals = Namespace()
custom_config_loaded = url_shortener_signals.signal('custom-config-loaded')

app = Flask(__name__)
app.config.from_object('url_shortener.default_config')

# See http://flask-sqlalchemy.pocoo.org/2.1/config/
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
