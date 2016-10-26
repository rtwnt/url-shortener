# -*- coding: utf-8 -*-
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from url_shortener import get_app_and_db

app, db = get_app_and_db('URL_SHORTENER_CONFIGURATION', from_envvar=True)

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
