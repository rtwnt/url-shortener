# -*- coding: utf-8 -*-
from url_shortener import app, custom_config_loaded, views

log_file = app.config['LOG_FILE']

if not app.debug and log_file is not None:
    import logging
    from logging.handlers import TimedRotatingFileHandler
    file_handler = TimedRotatingFileHandler(log_file, when='d')
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

app.config.from_envvar('URL_SHORTENER_CONFIGURATION')
custom_config_loaded.send(app)

app.run()
