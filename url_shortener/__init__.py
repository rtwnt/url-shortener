# -*- coding: utf-8 -*-

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config.from_object('url_shortener.default_config')
app.config.from_envvar('URL_SHORTENER_CONFIGURATION')
db = SQLAlchemy(app)

from . import event_handlers
