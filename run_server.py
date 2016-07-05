# -*- coding: utf-8 -*-
from url_shortener import app, event_handlers, views


if not app.debug:
    import logging
    from logging.handlers import TimedRotatingFileHandler
    file_handler = TimedRotatingFileHandler(app.config['LOG_FILE'])
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

app.run()
