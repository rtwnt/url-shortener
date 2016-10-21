# -*- coding: utf-8 -*-
from flask import Flask
from injector import Module, inject, Key
from spam_lists import (
    GoogleSafeBrowsing, HpHosts, GeneralizedURLTester, URLTesterChain,
    SPAMHAUS_DBL, SPAMHAUS_ZEN, SURBL_MULTI, SortedHostCollection
)
from wtforms.validators import ValidationError

from . import __version__, __title__


def sorted_host_list_from_file(name, classification, filename):
    """Create a sorted host list based on contents of a file

    :param name: name of a host list to be created
    :param classification: a string describing classification of all
    items stored by the host list
    :param filename: name of a file from which hosts fill be
    extracted. Each line of the file must contain one IP address
    or a hostname.
    :returns: a host list as an instance of SortedHostCollection
    """
    with open(filename) as f:
        hosts = f.read().splitlines()
    host_list = SortedHostCollection(name, classification, [])
    for item in hosts:
        host_list.add(item)

    return host_list


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

    def prepend(self, blacklist, message=None):
        """Prepend an object representing a blacklist to
        the URL tester chain

        :param blacklist: represents a blacklist to be used to
        recognize spam URLs. This object must have
        lookup_matching(urls) method
        :param message: a custom, blacklist-specific validation message
        to be associated with the blacklist, or None if the default
        message is to be associated with the blacklist
        """
        self._composite_blacklist.url_tester.url_testers.insert(0, blacklist)
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


hp_hosts = HpHosts(__title__)
url_validator = BlacklistValidator(
    GeneralizedURLTester(
        URLTesterChain(SURBL_MULTI, SPAMHAUS_ZEN, SPAMHAUS_DBL, hp_hosts)
    ),
    'The URL has been recognized as spam.'
)


host_blacklist = Key('host_blacklist')


class ValidationModule(Module):

    def configure(self, binder):
        binder.bind(
            BlacklistValidator,
            to=self.get_blacklist_url_validator()
        )

    @inject
    def get_gsb_client(self, app: Flask):
        gsb_client = GoogleSafeBrowsing(
            __title__,
            __version__,
            app.config['GOOGLE_SAFE_BROWSING_API_KEY']
        )

        app.logger.info('Google Safe Browsing API client loaded.')

        return gsb_client

    @inject
    def get_custom_host_blacklist(self, app: Flask):
        host_list = SortedHostCollection(
            'custom host blacklist',
            'blacklisted',
            []
        )
        blacklisted = app.config['BLACKLISTED_HOSTS']
        for item in blacklisted:
            host_list.add(item)

        app.logger.info(
            'Custom host blacklist loaded. The number of elements'
            ' it contains is: {}'.format(
                len(blacklisted)
            )
        )

        return host_list

    def get_blacklist_url_validator(self):
        return BlacklistValidator(
            GeneralizedURLTester(
                URLTesterChain(
                    self.get_custom_host_blacklist(),
                    self.get_gsb_client(),
                    SURBL_MULTI,
                    SPAMHAUS_ZEN,
                    SPAMHAUS_DBL,
                    hp_hosts
                )
            ),
            'The URL has been recognized as spam.'
        )


def configure_url_validator(app_object):
    app_object.logger.info('Configuring URL validation...')

    gsb_api_key = app_object.config['GOOGLE_SAFE_BROWSING_API_KEY']
    url_validator.prepend(
        GoogleSafeBrowsing(__title__, __version__, gsb_api_key)
    )
    app_object.logger.info('Google Safe Browsing API client loaded.')

    filename = app_object.config['HOST_BLACKLIST_FILE']
    if filename is not None:
        url_validator.prepend(
            sorted_host_list_from_file('blacklist', 'blacklisted', filename),
            'The host of target URL is blacklisted.'
        )
        msg = 'Custom host blacklist loaded from {}.'.format(filename)
        app_object.logger.info(msg)
