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
The value can be None, in which case the application won't write logs
to any file.

If the value is set, it must consist of an existing directory (if any),
but the file doesn't have to exist. The application uses timed roating
file handler with interval of one day, so the file specified here will
be created (if it doesn't exist yet) and used for one day. After that,
it will be renamed, and another file with the same name will be created
in the same directory and used.

:var REGISTRATION_RETRY_LIMIT: a maximum number of retries for
registering a new shortened url
:var GOOGLE_SAFE_BROWSING_API_KEY: a value necessary for querying
Google Safe Browsing API.
:var HOST_BLACKLIST_FILE: a name of file storing blacklisted hosts
(hostnames and ip addresses). The value must be either None, or
a name of an existing file containing blacklisted hosts in
a sorted order.

If the value is None, no host blacklist file will be used.
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
