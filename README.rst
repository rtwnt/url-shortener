url-shortener
================

A URL shortener application using Flask_, `Flask-SQLAlchemy`_, `Flask-WTF`_
and `spam-lists`_.

.. _Flask: http://flask.pocoo.org/
.. _Flask-SQLAlchemy: http://flask-sqlalchemy.pocoo.org/2.1/
.. _Flask-WTF: http://flask-wtf.readthedocs.io/en/latest/
.. _spam-lists: https://github.com/piotr-rusin/spam-lists

Features
--------

-  reusing alias for a requested short URL if its target has already been
   registered
-  a preview page for registered short URLs
-  configurable range of character numbers for newly registered aliases
-  logging using :code:`logging.handlers.TimedRotatingFileHandler`
-  preventing registration of URLs recognized as spam or having a blaclisted
   host
-  always previewing registered URLs that have been later blacklisted
   or recognized as spam
-  displaying proper warning when previewing spam or blacklisted URLs

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

You can also install dev extras, currently containing pylint_ and
restview_:

.. _pylint: https://www.pylint.org/
.. _restview: https://mg.pov.lt/restview/

.. code:: bash

    $ pip install url-shortener[dev]

It is necessary to override default configuration by setting
:code:`URL_SHORTENER_CONFIGURATION` environment variable to name of a custom
configuration file. This file must provide its own value of
:code:`SQLALCHEMY_DATABASE_URI`, :code:`SECRET_KEY` and
:code:`GOOGLE_SAFE_BROWSING_API_KEY options`.

For more details, read `docstring in url_shortener.default_config.py`__

.. __: https://github.com/piotr-rusin/url-shortener/blob/master/
   url_shortener/default_config.py

License
-------

| MIT
| See LICENSE__

.. __: https://github.com/piotr-rusin/spam-lists/blob/master/LICENSE
