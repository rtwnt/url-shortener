# -*- coding: utf-8 -*-
from spam_lists import (
    GoogleSafeBrowsing, HpHosts, GeneralizedURLTester, URLTesterChain,
    SPAMHAUS_DBL, SPAMHAUS_ZEN, SURBL_MULTI, SortedHostCollection
)
from wtforms.validators import ValidationError

from . import app


hp_hosts = HpHosts('url-shortener')
google_safe_browsing = GoogleSafeBrowsing(
    'url-shortener',
    '0.9',
    app.config['GOOGLE_SAFE_BROWSING_API_KEY']
)

spam_tester = GeneralizedURLTester(
    URLTesterChain(
        SPAMHAUS_DBL,
        SPAMHAUS_ZEN,
        SURBL_MULTI,
        hp_hosts,
        google_safe_browsing
    )
)

filename = app.config['HOST_BLACKLIST_FILE']
hosts = []
if filename is not None:
    with open(filename) as f:
        hosts = f.read().splitlines()

blacklist_tester = GeneralizedURLTester(
    SortedHostCollection(
        'blacklist',
        'blacklisted',
        hosts
    )
)


def get_msg_if_blacklisted_or_spam(url):
    """ Get a message if given URL has blacklisted host
    or is recognized as spam

    :param url: a URL value to be tested
    :returns: a string message if any of the testers recognize
    the URL as match, or None
    """
    msg_map = {
        blacklist_tester: 'The host of target URL is blacklisted.',
        spam_tester: 'The URL has been recognized as spam.'
    }

    for tester, msg in msg_map.items():
        if tester.any_match([url]):
            return msg


def not_blacklisted_nor_spam(form, field):
    """ Check if the data in the field is not
    blacklisted nor a spam

    This function is a custom WTForms field validator using
    get_msg_if_blacklisted_or_spam for validating data in the field.
    If the message returned for the data is not None, the function
    raises ValidationError with the message.

    :param form: a form whose field is to be validated
    :param field: a field containing data to be validated
    :raises ValidationError: if the function returns a message
    for the data
    """
    msg = get_msg_if_blacklisted_or_spam(field.data)
    if msg is not None:
        raise ValidationError(msg)


def sorted_host_list_from_file(name, classification, filename):
    """Create a sorted host list based on contents of a file

    :param name: name of a host list to be created
    :param classification: a string describing classification of all
    items stored by the host list
    :returns: a host list as an instance of SortedHostCollection
    """
    hosts = []
    with open(filename) as f:
        hosts = f.read().splitlines()

    return SortedHostCollection(name, classification, hosts)
