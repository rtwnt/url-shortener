# -*- coding: utf-8 -*-
from url_shortener import app

""" Host blacklist file is unnecessary during testing.
It doesn't exist in the directory structure of test package,
so attempting to load it during testing would cause FileNotFoundError.

We set the file name to None to prevent that.
"""
app.config['HOST_BLACKLIST_FILE'] = None
