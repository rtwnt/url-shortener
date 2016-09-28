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


class BlacklistValidator(object):
    """A URL spam detector using configurable blacklists

    :ivar _msg_map: a dictionary mapping blacklists used by an instance
    of the class to validation messages associated with them
    """

    def __init__(self, composite_blacklist, default_message):
        """ Initialize a new instance

        :param composite_blacklist: an object representing multiple
        blacklist used by an instance of this class

        It must have lookup_matching(urls) method accepting a sequence
        of URLs and returning an iterator returning other objects, each
        with a source property storing one of the blacklists used by
        the validator - the one containing the item that matches one
        of the URLs.

        It must also have a url_tester property with another property:
        url_testers. The last property represents a chain of blacklist
        objects used by the composite. This property must have
        insert(index, item) method, where :
        * index is a position at which a new blacklist object is
        inserted
        * object is a blacklist object to be inserted
        :param default_message: a default validation message to be provided
        when a URL matches a blacklist that does not have its specific
        validation message
        """
        self._composite_blacklist = composite_blacklist
        self._msg_map = {}
        self.default_message = default_message

    def append_blacklist(self, blacklist, message=None):
        """Append an object representing a blacklist to
        the URL tester chain

        :param blacklist: represents a blacklist to be used to
        recognize spam URLs. This object must have
        lookup_matching(urls) method
        :param message: a custom, blacklist-specific validation message
        to be associated with the blacklist
        """
        self._composite_blacklist.url_tester.url_testers.append(blacklist)
        if message is not None:
            self._msg_map[blacklist] = message

    def get_msg_if_blacklisted(self, url):
        """ Get a message if URL or one of its redirect addresses
        is blacklisted

        :param url: a URL address as a string
        :returns: a string message if the URL or its redirect addresses
        match content of any of the blacklists, or None
        """
        for match in self._composite_blacklist.lookup_matching([url]):
            return self._msg_map.get(match.source, self.default_message)

    def assert_not_blacklisted(self, form, field):
        """Assert the URL value from the field is not blacklisted

        This method is a custom WTForms field validator.

        :param form: a form whose field is to be validated
        :param field: a field containing data to be validated
        :raises ValidationError: if the function returns a message
        for the data
        """
        msg = self.get_msg_if_blacklisted(field.data)
        if msg is not None:
            raise ValidationError(msg)


common_blacklist_validator = BlacklistValidator(
    GeneralizedURLTester(URLTesterChain()),
    'The URL has been recognized as spam.'
)
