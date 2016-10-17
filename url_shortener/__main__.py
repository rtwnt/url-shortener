# -*- coding: utf-8 -*-
from flask_injector import FlaskInjector

from url_shortener import app, views
from url_shortener.validation import configure_url_validator
from url_shortener.models import configure_random_factory

log_file = app.config['LOG_FILE']

if not app.debug and log_file is not None:
    import logging
    from logging.handlers import TimedRotatingFileHandler
    file_handler = TimedRotatingFileHandler(log_file, when='d')
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

app.config.from_envvar('URL_SHORTENER_CONFIGURATION')
configure_url_validator(app)
configure_random_factory(app)

FlaskInjector(app=app)

app.run()
