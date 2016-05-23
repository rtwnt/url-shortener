# -*- coding: utf-8 -*-
from submodules.spam_lists_lib.spam_lists import GoogleSafeBrowsing, HpHosts

from . import app

google_safe_browsing = GoogleSafeBrowsing(
    'url-shortener',
    '0.9',
    app.config['GOOGLE_SAFE_BROWSING_API_KEY']
)

hp_hosts = HpHosts('url-shortener')
