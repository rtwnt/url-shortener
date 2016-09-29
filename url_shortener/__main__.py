# -*- coding: utf-8 -*-
from url_shortener import app, before_app_run, views
from url_shortener.models import Alias


log_file = app.config['LOG_FILE']

if not app.debug and log_file is not None:
    import logging
    from logging.handlers import TimedRotatingFileHandler
    file_handler = TimedRotatingFileHandler(log_file, when='d')
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

Alias.init_random_factory(
    app.config['MIN_NEW_ALIAS_LENGTH'],
    app.config['MAX_NEW_ALIAS_LENGTH']
)

before_app_run.send(app)
app.run()
