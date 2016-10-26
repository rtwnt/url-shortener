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
from flask_injector import FlaskInjector

from .views import url_shortener
from .forms import configure as configure_form
from .domain_and_persistence import DomainAndPersistenceModule, SQLAlchemy
from .validation import ValidationModule


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


def _get_injector(app):
    """Set up and return an instance of FlaskInjector

    :param app: an application for which the function will set up
    the injector
    :return: an instance of FlaskInjector to be used by the application
    """

    return FlaskInjector(
        app=app,
        modules=[
            DomainAndPersistenceModule(app),
            ValidationModule(app),
            configure_form
        ],
        use_annotations=True
    )


def get_app_and_db(configuration, from_envvar=False):
    """Get application instance and database object used by it

    :param configuration: a string value referring to a file from which
    configuration options will be loaded. This value may be either
    the name of the file, or name of an environment variable set to
    the name of configuration file
    :param from_envvar: if True: configuration parameter will
    be treated as name of an evnironment variable pointing to
    the configuration file, if False: it will be treated as name of
    the configuration file itself.
    :returns: a tuple with application object as its first and
    database object as its second element
    """

    app = Flask(__name__)
    app.config.from_object('url_shortener.default_config')
    if from_envvar:
        app.config.from_envvar(configuration)
    else:
        app.config.from_pyfile(configuration)

    _set_up_logging(app)
    app.register_blueprint(url_shortener)
    injector = _get_injector(app)

    return app, injector.injector.get(SQLAlchemy)
