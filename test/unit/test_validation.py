# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock

from nose_parameterized import parameterized

from url_shortener.validation import BlacklistValidator, ValidationError


class BlacklistValidatorTest(unittest.TestCase):
    """ Tests for BlacklistValidator class

    :ivar cb_mock: an instance of Mock for composite_blacklist
    dependency of Mock
    :ivar tested_instance: instance of BlacklistValidator to be used
    for testing

    :cvar DEFAULT_MESSAGE: a string to be passed as a default message
    to constructor of tested instance
    """

    DEFAULT_MESSAGE = 'A default message'

    def setUp(self):
        self.cb_mock = Mock()
        self.cb_mock.lookup_matching.return_value = []
        self.tested_instance = BlacklistValidator(
            self.cb_mock,
            self.DEFAULT_MESSAGE
        )
        self.tested_instance.redirect_resolver = Mock()

    @parameterized.expand([
        ('', None),
        ('when_passing_a_message', 'A message')
    ])
    def test_append_blacklist_adds_blacklist(self, _, message):
        """append_blacklist method is expected to call
        append(object) method of underlying url tester chain
        object, passing the blacklist to be added as its argument
        """
        blacklist = Mock()

        self.tested_instance.append_blacklist(blacklist, message)

        append = self.cb_mock.url_tester.url_testers.append
        append.assert_called_once_with(blacklist)

    def test_append_blacklist_adds_message(self):
        """append_blacklist method is expected to add a message
        associated with the blacklist object being added. Relationship
        between the blacklist and the message is expected to be stored
        in _msg_map property of the tested instance.
        """
        blacklist = Mock()
        message = 'A message'

        self.tested_instance.append_blacklist(blacklist, message)

        self.assertDictContainsSubset(
            {blacklist: message},
            self.tested_instance._msg_map
        )

    def test_append_blacklist_does_not_add_message(self):
        """append_blacklist method is expected not to add a
        blacklist-specific validation message when the value passed as
        message is None
        """
        blacklist = Mock()

        self.tested_instance.append_blacklist(blacklist)

        self.assertNotIn(blacklist, self.tested_instance._msg_map)

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
