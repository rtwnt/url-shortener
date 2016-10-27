# -*- coding: utf-8 -*-
"""A module instantiating application object and
starting builtin server
"""
from url_shortener import get_app_and_db

app, _ = get_app_and_db('URL_SHORTENER_CONFIGURATION', from_envvar=True)

app.run()
