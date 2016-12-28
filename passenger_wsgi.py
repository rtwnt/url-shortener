# -*- coding: utf-8 -*-

from url_shortener import get_app_and_db

application, _ = get_app_and_db('URL_SHORTENER_CONFIGURATION', from_envvar=True)
