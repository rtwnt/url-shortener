# -*- coding: utf-8 -*-
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from url_shortener import app
from url_shortener.models import db

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
