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

import logging
from logging.handlers import TimedRotatingFileHandler

from flask import Flask
from .views import url_shortener

app = Flask(__name__)
app.config.from_object('url_shortener.default_config')
app.register_blueprint(url_shortener)


def _set_up_logging(app):
    """Set up logging for given Flask application object

    :param app: an application for which the function will
    set up logging
    """
    log_file = app.config['LOG_FILE']

    if not app.debug and log_file is not None:
        file_handler = TimedRotatingFileHandler(log_file, when='d')
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)


