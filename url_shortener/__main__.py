# -*- coding: utf-8 -*-
from flask_injector import FlaskInjector

from url_shortener import app, views
from url_shortener.forms import FormModule
from url_shortener.domain_and_persistence import DomainAndPersistenceModule
from url_shortener.validation import ValidationModule

log_file = app.config['LOG_FILE']

if not app.debug and log_file is not None:
    import logging
    from logging.handlers import TimedRotatingFileHandler
    file_handler = TimedRotatingFileHandler(log_file, when='d')
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

app.config.from_envvar('URL_SHORTENER_CONFIGURATION')

FlaskInjector(
    app=app,
    modules=[
        DomainAndPersistenceModule(app),
        ValidationModule(app),
        FormModule()
    ],
    use_annotations=True
)

app.run()
