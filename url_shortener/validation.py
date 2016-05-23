# -*- coding: utf-8 -*-
from submodules.spam_lists_lib.spam_lists import (
    GoogleSafeBrowsing, HpHosts, GeneralizedUrlTester, UrlTesterChain,
    SPAMHAUS_DBL, SPAMHAUS_ZEN, SURBL_MULTI
)

from . import app

google_safe_browsing = GoogleSafeBrowsing(
    'url-shortener',
    '0.9',
    app.config['GOOGLE_SAFE_BROWSING_API_KEY']
)

hp_hosts = HpHosts('url-shortener')
spam_tester = GeneralizedUrlTester(
    UrlTesterChain(
        SPAMHAUS_DBL,
        SPAMHAUS_ZEN,
        SURBL_MULTI,
        hp_hosts,
        google_safe_browsing
    )
)
