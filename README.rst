url-shortener
================

A URL shortener application using Flask_, `Flask-SQLAlchemy`_, `Flask-WTF`_ , `Flask-Migrate`_, `Flask-Script`_, `Flask-Injector`_ and `spam-lists`_.

.. _Flask: http://flask.pocoo.org/
.. _Flask-SQLAlchemy: http://flask-sqlalchemy.pocoo.org/2.1/
.. _Flask-WTF: http://flask-wtf.readthedocs.io/en/latest/
.. _Flask-Migrate: https://flask-migrate.readthedocs.io/en/latest/
.. _Flask-Script: https://flask-script.readthedocs.io/en/latest/
.. _Flask-Injector: https://github.com/alecthomas/flask_injector
.. _spam-lists: https://github.com/piotr-rusin/spam-lists

Features
--------

-  providing unique short alias for each registered URL
-  a preview page for registered short URLs
-  configurable range of character numbers for newly registered aliases
-  logging using :code:`logging.handlers.TimedRotatingFileHandler`
-  preventing registration of URLs recognized as spam or having a blaclisted host
-  always previewing registered URLs that have been blacklisted or recognized as spam after their registration
-  displaying proper warning when previewing spam or blacklisted URLs
-  customizable whitelist for trusted, non-spam hosts
-  support for database migration commands:

   .. code:: bash

       $ python manage.py db init
       $ python manage.py db migrate
       $ python manage.py db upgrade
       $ python manage.py db --help

Installation
------------

Clone from GitHub and install using pip:

.. code:: bash

    $ git clone https://github.com/piotr-rusin/url-shortener
    $ cd url-shortener
    $ pip install .

To be able to run tests, install test extras:

.. code:: bash

    $ pip install url-shortener[test]

It is necessary to override default configuration by setting :code:`URL_SHORTENER_CONFIGURATION` environment variable to a name of a custom configuration file. This file must provide its own value of the following options:

-  :code:`SQLALCHEMY_DATABASE_URI`
-  :code:`SECRET_KEY`
-  :code:`GOOGLE_SAFE_BROWSING_API_KEY`
-  :code:`RECAPTCHA_PUBLIC_KEY`
-  :code:`RECAPTCHA_PRIVATE_KEY`

For more details, read `docstring in url_shortener.default_config.py`__

.. __: https://github.com/piotr-rusin/url-shortener/blob/master/
   url_shortener/default_config.py

When installing a new version of the project, run the following command to upgrade your database in case the new version introduces changes to its database schema:

.. code:: bash

    $ python manage.py db upgrade

License
-------

| MIT
| See LICENSE__

.. __: https://github.com/piotr-rusin/spam-lists/blob/master/LICENSE
