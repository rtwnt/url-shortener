url-shortener
================

A url shortener application using Flask_, `Flask-SQLAlchemy`_, `Flask-WTF`_
and `spam-lists`_.

.. _Flask: http://flask.pocoo.org/
.. _Flask-SQLAlchemy: http://flask-sqlalchemy.pocoo.org/2.1/
.. _Flask-WTF: http://flask-wtf.readthedocs.io/en/latest/
.. _spam-lists: https://github.com/piotr-rusin/spam-lists

Features
--------

-  reusing alias for a requested short url if its target has already been
   registered
-  a preview page for registered short urls
-  configurable range of character numbers for newly registered aliases
-  logging using logging.handlers.TimedRotatingFileHandler
-  preventing registration of urls recognized as spam or having a blaclisted
   host
-  always previewing registered urls that have been later blacklisted
   or recognized as spam
-  displaying proper warning when previewing spam or blacklisted urls

License
-------

| Apache 2.0
| See LICENSE__

.. __: https://github.com/piotr-rusin/spam-lists/blob/master/LICENSE
