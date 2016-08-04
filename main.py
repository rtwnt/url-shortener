# -*- coding: utf-8 -*-
'''
url-shortener
==============

An application for generating and storing shorter aliases for
requested urls. Uses `spam-lists`__ to prevent generating a short url
for an address recognized as spam, or to warn a user a pre-existing
short alias has a target that has been later recognized as spam.

.. __: https://github.com/piotr-rusin/spam-lists
'''
from url_shortener import app, event_handlers, views

__title__ = 'url-shortener'
__version__ = '0.9.0.dev1'
__author__ = 'Piotr Rusin'
__email__ = "piotr.rusin88@gmail.com"
__license__ = 'MIT'
__copyright__ = 'Copyright 2016 Piotr Rusin'


log_file = app.config['LOG_FILE']

if not app.debug and log_file is not None:
    import logging
    from logging.handlers import TimedRotatingFileHandler
    file_handler = TimedRotatingFileHandler(app.config['LOG_FILE'], when='d')
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

app.run()
