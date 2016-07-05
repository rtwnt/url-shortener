# -*- coding: utf-8 -*-
''' Default configuration for the application

This data must be supplemented with custom configuration to which
URL_SHORTENER_CONFIGURATION environment variable points, overriding
some of the values specified here.

:var SQLALCHEMY_DATABASE_URI: uri of database to be used by the application.

The default value serves only as documentation, and it was taken from:
http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls

:var MIN_NEW_ALIAS_LENGTH: a minimum number of characters in a newly
generated alias
:var MAX_NEW_ALIAS_LENGTH: a maximum number of characters in a newly
generated alias
:var SECRET_KEY: a secret key to be used by the application
:var LOG_FILE: a name of file to which the application writes logs.
:var REGISTRATION_RETRY_LIMIT: a maximum number of retries for
registering a new shortened url
:var GOOGLE_SAFE_BROWSING_API_KEY: a value necessary for querying
Google Safe Browsing API.
:var HOST_BLACKLIST_FILE: a name of file storing blacklisted hosts
(hostnames and ip addresses). Each line must contain one host.
'''
SQLALCHEMY_DATABASE_URI = (
    'dialect+driver://username:password@host:port/database'
)
MIN_NEW_ALIAS_LENGTH = 1
MAX_NEW_ALIAS_LENGTH = 4
SECRET_KEY = 'a secret key'
LOG_FILE = None
REGISTRATION_RETRY_LIMIT = 10
GOOGLE_SAFE_BROWSING_API_KEY = 'a key'
HOST_BLACKLIST_FILE = None
