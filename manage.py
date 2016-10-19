# -*- coding: utf-8 -*-
"""FIXME: this module doesn't work since db object imported from
url_shortener package does not contain any mappings. It receives mappings
only in url_shortener/__main__.py, because right now this is where Injector
is instantiated and configured for application instance, creating TargetURL
class.

This will be fixed when introducing application factory. Until then, no
temporary fixes will be made.
"""
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from url_shortener import app
from url_shortener.models import db

app.config.from_envvar('URL_SHORTENER_CONFIGURATION')

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
