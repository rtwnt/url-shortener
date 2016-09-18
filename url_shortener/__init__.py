# -*- coding: utf-8 -*-

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config.from_object('url_shortener.default_config')
"""
From http://flask-sqlalchemy.pocoo.org/2.1/config/:

"SQLALCHEMY_TRACK_MODIFICATIONS - If set to True, Flask-SQLAlchemy
will track modifications of objects and emit signals. The default is
None, which enables tracking but issues a warning that it will be
disabled by default in the future. This requires extra memory and
should be disabled if not needed."

This application uses SQLAlchemy event system, so this value is set
to False
"""
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_envvar('URL_SHORTENER_CONFIGURATION')
db = SQLAlchemy(app)
