# -*- coding: utf-8 -*-
# pylint: disable=C0103

"""Tests for view classes and functions."""
import unittest
from unittest.mock import Mock, patch, MagicMock

from nose_parameterized import parameterized
from werkzeug.exceptions import HTTPException

from url_shortener.views import shorten_url, ShowURL


class BaseViewTest(object):
    """A class providing mocks used by all tested view functions."""

    def setUp(self):
        self.render_template_patcher = patch(
            'url_shortener.views.render_template'
        )
        self.render_template_mock = self.render_template_patcher.start()

        self.target_url_class_mock = Mock()

    def tearDown(self):
        self.render_template_patcher.stop()


class RedirectPatchMixin(object):
    """A mixin providing a mock for flask.redirect function."""

    def setUp(self):
        self.redirect_patcher = patch('url_shortener.views.redirect')
        self.redirect_mock = self.redirect_patcher.start()

        super(RedirectPatchMixin, self).setUp()

    def tearDown(self):
        self.redirect_patcher.stop()

        super(RedirectPatchMixin, self).tearDown()


class ShortenURLTest(RedirectPatchMixin, BaseViewTest, unittest.TestCase):
    """Tests for shorten_url function."""

    def setUp(self):
        self.form_class_mock = Mock()
        self.form_mock = self.form_class_mock()
        self.form_mock.errors.values = MagicMock()

        self.commit_changes_mock = Mock()

        self.markup_patcher = patch('url_shortener.views.Markup')
        self.markup_mock = self.markup_patcher.start()

        self.url_for_patcher = patch('url_shortener.views.url_for')
        self.url_for_mock = self.url_for_patcher.start()

        self.flash_patcher = patch('url_shortener.views.flash')
        self.flash_mock = self.flash_patcher.start()

        super(ShortenURLTest, self).setUp()

    def tearDown(self):
        self.markup_patcher.stop()
        self.url_for_patcher.stop()
        self.flash_patcher.stop()

        super(ShortenURLTest, self).tearDown()

    def _call(self):
        """Call tested function with all arguments."""
        return shorten_url(
            self.target_url_class_mock,
            self.form_class_mock,
            self.commit_changes_mock
        )

    def test_gets_or_creates_a_target_url(self):
        """Test if get_or_create method of target URL class is called."""
        self._call()

        self.target_url_class_mock.get_or_create.assert_called_once_with(
            self.form_mock.url.data
        )

    def test_registers_new_short_url(self):
        """Test if commit_changes function is called."""
        self._call()
        self.assertTrue(self.commit_changes_mock.called)

    def test_redirects_to_the_same_route(self):
        """Test if a user is redirected to form page."""
        self._call()
        self.url_for_mock.assert_called_once_with('url_shortener.shorten_url')
        redirect_url = self.url_for_mock.return_value
        self.redirect_mock.assert_called_once_with(redirect_url)

    def test_returns_redirect_response(self):
        """Test if a redirection result is returned."""
        expected = self.redirect_mock.return_value
        actual = self._call()
        self.assertEqual(expected, actual)

    def test_prepares_success_message(self):
        """Test if a message with specified elements is prepared."""
        url_mock = self.target_url_class_mock.get_or_create.return_value

        self._call()

        assert_called = (
            self.markup_mock.return_value.format.assert_any_call
        )

        assert_called('Original URL', url_mock, ' class=truncated')
        assert_called('Short URL', url_mock.short_url, '')
        assert_called('Preview available at', url_mock.preview_url, '')

    def test_flashes_success_message(self):
        """Test if all elements of the success message are flashed."""
        message_mock = self.markup_mock.return_value.format.return_value

        self._call()

        self.flash_mock.assert_called_with(message_mock)
        self.assertEqual(3, self.flash_mock.call_count)

    def test_renders_form_template(self):
        """Test if render_template is called for a GET request."""
        self.form_mock.validate_on_submit.return_value = False
        self._call()
        self.render_template_mock.assert_called_once_with(
            'shorten_url.html',
            form=self.form_mock
        )

    def test_returns_rendered_template(self):
        """Test if rendered template is returned for a GET request."""
        self.form_mock.validate_on_submit.return_value = False
        expected = self.render_template_mock.return_value
        actual = self._call()
        self.assertEqual(expected, actual)


class TestShowURL(RedirectPatchMixin, BaseViewTest, unittest.TestCase):
    """Tests for ShowURL class view.

    :cvar PREVIEW_NOT_PREVIEW_SETUP: parameters for tests differing only
    with the value of 'preview' constructor argument
    :cvar WHEN_PREVIEW_SETUP: parameters for tests differing in
    combinations of conditions expected to lead to rendering and
    returning of a preview template
    :ivar validator_mock: mock for a BlacklistValidator instance to be
    used by the view instance
    :ivar get_msg_if_blacklisted_mock: a mock for get_msg_if_blacklisted
    method of blacklist validator.
    """

    PREVIEW_NOT_PREVIEW_SETUP = [
        ('preview', True),
        ('redirect', False)
    ]
    WHEN_PREVIEW_SETUP = [
        ('always', True, ''),
        ('always_and_with_spam_message', True, 'This is spam'),
        ('with_spam_message', False, 'This is spam.')
    ]

    def setUp(self):
        bval = Mock()
        self.validator_mock = bval
        self.get_msg_if_blacklisted_mock = bval.get_msg_if_blacklisted
        self.get_msg_if_blacklisted_mock.return_value = ''

        super(TestShowURL, self).setUp()

        self.get_or_404_mock = self.target_url_class_mock.query.get_or_404

    def create_view_and_call_dispatch_request(self, preview, alias='abc'):
        """Prepare view instance and call dispatch request method.

        :param preview: a preview parameter of ShowURL constructor
        :param alias: an alias parameter to be passed to the method
        """
        obj = ShowURL(
            preview,
            self.target_url_class_mock,
            self.validator_mock
            )

        return obj.dispatch_request(alias)

    @parameterized.expand(PREVIEW_NOT_PREVIEW_SETUP)
    def test_dispatch_request_queries_for_target_url_to(self, _, preview):
        """Test if the method queries for target URL with the alias.

        :param preview: a preview parameter for ShowURL constructor
        """
        alias = 'xyz'

        self.create_view_and_call_dispatch_request(preview, alias)

        self.get_or_404_mock.assert_called_once_with(alias)

    @parameterized.expand(PREVIEW_NOT_PREVIEW_SETUP)
    def test_dispatch_request_raises_http_error_for(self, _, preview):
        """Test for a HTTPError occurence.

        :param preview: a preview parameter for ShowURL constructor
        """
        self.get_or_404_mock.side_effect = HTTPException

        with self.assertRaises(HTTPException):
            self.create_view_and_call_dispatch_request(preview)

    @parameterized.expand(PREVIEW_NOT_PREVIEW_SETUP)
    def test_dispatch_request_validates_url(self, _, preview):
        """Test if the URL is validated.

        :param preview: a preview parameter for ShowURL constructor
        """
        self.create_view_and_call_dispatch_request(preview)
        target_url = self.get_or_404_mock()

        self.get_msg_if_blacklisted_mock.assert_called_once_with(
            str(target_url)
        )

    @parameterized.expand(WHEN_PREVIEW_SETUP)
    def test_dispatch_request_renders_preview(self, _, preview, spam_msg):
        """Test if the method calls render_preview.

        :param preview: a preview parameter for ShowURL constructor
        :param spam_msg: a message to be provided by the validator
        """
        self.get_msg_if_blacklisted_mock.return_value = spam_msg

        self.create_view_and_call_dispatch_request(preview)

        self.render_template_mock.assert_called_once_with(
            'preview.html',
            target_url=self.get_or_404_mock(),
            warning=spam_msg
        )

    @parameterized.expand(WHEN_PREVIEW_SETUP)
    def test_dispatch_request_shows_preview(self, _, preview, spam_msg):
        """Test if the method returns preview.

        :param preview: a preview parameter for ShowURL constructor
        :param spam_msg: a message to be provided by the validator
        """
        self.get_msg_if_blacklisted_mock.return_value = spam_msg

        expected = self.render_template_mock()
        actual = self.create_view_and_call_dispatch_request(preview)

        self.assertEqual(expected, actual)

    def test_dispatch_request_redirects(self):
        """Test if redirect function is called."""
        self.create_view_and_call_dispatch_request(False)

        self.redirect_mock.assert_called_once_with(self.get_or_404_mock())

    def test_dispatch_request_returns_redirect(self):
        """Test if the method returns result of redirection."""
        self.get_msg_if_blacklisted_mock.return_value = None

        expected = self.redirect_mock()
        actual = self.create_view_and_call_dispatch_request(False)

        self.assertEqual(expected, actual)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
