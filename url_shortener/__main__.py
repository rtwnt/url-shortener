# -*- coding: utf-8 -*-
from flask_injector import FlaskInjector

from url_shortener import app, views, models
from url_shortener.validation import configure_url_validator

log_file = app.config['LOG_FILE']

if not app.debug and log_file is not None:
    import logging
    from logging.handlers import TimedRotatingFileHandler
    file_handler = TimedRotatingFileHandler(log_file, when='d')
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

app.config.from_envvar('URL_SHORTENER_CONFIGURATION')
configure_url_validator(app)

FlaskInjector(app=app, modules=[models.configure])

app.run()
