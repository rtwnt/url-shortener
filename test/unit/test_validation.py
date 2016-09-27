# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock

from url_shortener.validation import BlacklistValidator, ValidationError


class BlacklistValidatorTest(unittest.TestCase):
    """ Tests for BlacklistValidator class

    :ivar cb_mock: an instance of Mock for composite_blacklist
    dependency of Mock
    :ivar tested_instance: instance of BlacklistValidator to be used
    for testing
    """
    def setUp(self):
        self.cb_mock = Mock()
        self.cb_mock.lookup_matching.return_value = []
        self.tested_instance = BlacklistValidator(self.cb_mock)
        self.tested_instance.redirect_resolver = Mock()

    def test_prepend_blacklist_adds_blacklist(self):
        """ prepend_blacklist method is expected to call
        inser(index, object) method of underlying url teser chain
        object with index = 0 and object being a blacklist object
        to be added
        """
        blacklist = Mock()
        message = 'A message'

        self.tested_instance.prepend_blacklist(blacklist, message)

        insert = self.cb_mock.url_tester.url_testers.insert
        insert.assert_called_once_with(0, blacklist)

    def test_prepend_blacklist_adds_message(self):
        """ prepend_blacklist method is expected to add a message
        associated with the blacklist object being added to valdiator's
        _msg_map property, with blacklist object being the key and
        the message being a value.
        """
        blacklist = Mock()
        message = 'A message'

        self.tested_instance.prepend_blacklist(blacklist, message)

        self.assertDictContainsSubset(
            {blacklist: message},
            self.tested_instance._msg_map
        )

    def set_up_matching_url(self, url, expected_message='A message'):
        """ Prepare a spam URL value recognized by tested instance
        and a message associated with the result of its validation

        :param url: a URL value expected to be recognized by
        tested instance
        :param expected_message: a message to be associated with
        the result of validating the URL
        """
        blacklist = Mock()
        self.tested_instance._msg_map[blacklist] = expected_message

        first = Mock()
        first.address = url
        first.source = blacklist

        self.cb_mock.lookup_matching.return_value = first, Mock()

    def test_get_msg_if_blacklisted_returns_msg(self):
        """ get_msg_if_blacklisted is expected to return a message
        when it detects a blacklisted URL
        """
        url = 'http://first.com'
        expected_message = 'A message'
        self.set_up_matching_url(url, expected_message)

        actual_message = self.tested_instance.get_msg_if_blacklisted(url)
        self.assertEqual(expected_message, actual_message)

    def test_get_msg_if_blacklisted_returns_none(self):
        """ get_msg_if_blacklisted is expected to return None when it
        does not detect any blacklisted URLs
        """
        actual_message = self.tested_instance.get_msg_if_blacklisted(
            'http://not.spam.com'
        )
        self.assertIsNone(actual_message)

    def _test_assert_not_blacklisted(self, url='http://example.com'):
        """ Setup test environment for assert_not_blacklisted and
        call the method
        """
        form = Mock()
        field = Mock()
        field.data = url

        self.tested_instance.assert_not_blacklisted(form, field)

    def test_assert_not_blacklisted_raises_ValidationError(self):
        """ assert_not_blacklisted is expected to raise
        wtforms.validators.ValidationError when it detects
        a blacklisted URL
        """
        url = 'http://blacklisted.com'
        self.set_up_matching_url(url)

        with self.assertRaises(ValidationError):
            self._test_assert_not_blacklisted(url)

    def test_assert_not_blacklisted_does_not_raise_an_error(self):
        """ assert_not_blacklisted is expected not to raise
        a ValidationError when it detects no blacklisted URL
        """
        try:
            self._test_assert_not_blacklisted()
        except ValidationError:
            self.fail(
                'Test failed: ValidationError was unexpectedly raised'
                ' by assert_not_blacklisted'
            )


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
