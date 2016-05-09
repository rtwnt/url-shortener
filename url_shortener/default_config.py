# -*- coding: utf-8 -*-
''' Default configuration for the application

This data must be supplemented with custom configuration to which
URL_SHORTENER_CONFIGURATION environment variable points, overriding
some of the values specified here.

:var SQLALCHEMY_DATABASE_URI: uri of database to be used by the application.

The default value servers only as documentation, and it was taken from:
http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls
'''
SQLALCHEMY_DATABASE_URI = (
    'dialect+driver://username:password@host:port/database'
)
