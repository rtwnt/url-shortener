# -*- coding: utf-8 -*-
from submodules.spam_lists_lib.spam_lists import (
    GoogleSafeBrowsing, HpHosts, GeneralizedUrlTester, UrlTesterChain,
    SPAMHAUS_DBL, SPAMHAUS_ZEN, SURBL_MULTI
)

from wtforms.validators import ValidationError

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


class NotABlacklistMatch():
    def __init__(self, blacklist, message=None):
        self.blacklist = blacklist
        self.message = message

    def __call__(self, form, field):
        if self.is_match(field.data):
            raise ValidationError(self.message)

    def is_match(self, value):
        return self.blacklist.any_match([value])


not_spam = NotABlacklistMatch(spam_tester, 'This value is recognized as spam')
