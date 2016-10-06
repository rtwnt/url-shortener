# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock, patch, MagicMock

from werkzeug.exceptions import HTTPException

from url_shortener.views import (
    shorten_url, get_response, RegistrationRetryLimitExceeded
)


class BaseViewTest(object):
    """ A class providing mocks used by all tested view functions """
    def setUp(self):
        self.render_template_patcher = patch(
            'url_shortener.views.render_template'
        )
        self.render_template_mock = self.render_template_patcher.start()

        self.shortened_url_class_patcher = patch(
            'url_shortener.views.ShortenedURL'
        )
        self.shortened_url_class_mock = (
            self.shortened_url_class_patcher.start()
        )

    def tearDown(self):
        self.render_template_patcher.stop()
        self.shortened_url_class_patcher.stop()


class RedirectPatchMixin(object):
    """ A mixin providing a mock for flask.redirect function """
    def setUp(self):
        self.redirect_patcher = patch('url_shortener.views.redirect')
        self.redirect_mock = self.redirect_patcher.start()

        super(RedirectPatchMixin, self).setUp()

    def tearDown(self):
        self.redirect_patcher.stop()

        super(RedirectPatchMixin, self).tearDown()


class ShortenURLTest(RedirectPatchMixin, BaseViewTest, unittest.TestCase):
    def setUp(self):
        self.form_class_patcher = patch('url_shortener.views.ShortenedURLForm')
        self.form_class_mock = self.form_class_patcher.start()
        self.form_mock = self.form_class_mock()

        self.register_if_new_patcher = patch(
            'url_shortener.views.register_if_new'
        )
        self.register_if_new_mock = self.register_if_new_patcher.start()

        self.app_patcher = patch('url_shortener.views.app')
        self.app_mock = self.app_patcher.start()
        self.app_mock.config = MagicMock()

        self.markup_patcher = patch('url_shortener.views.Markup')
        self.markup_mock = self.markup_patcher.start()

        self.url_for_patcher = patch('url_shortener.views.url_for')
        self.url_for_mock = self.url_for_patcher.start()

        self.session_patcher = patch('url_shortener.views.session', {})
        self.session = self.session_patcher.start()

        self.flash_patcher = patch('url_shortener.views.flash')
        self.flash_mock = self.flash_patcher.start()

        super(ShortenURLTest, self).setUp()

    def tearDown(self):
        self.form_class_patcher.stop()
        self.register_if_new_patcher.stop()
        self.app_patcher.stop()
        self.markup_patcher.stop()
        self.url_for_patcher.stop()
        self.session_patcher.stop()
        self.flash_patcher.stop()

        super(ShortenURLTest, self).tearDown()

    def test_registers_new_short_url(self):
        shortened_url_mock = (
            self.shortened_url_class_mock.get_or_create.return_value
        )
        shorten_url()
        self.register_if_new_mock.assert_called_once_with(shortened_url_mock)

    def test_saves_new_alias_in_session(self):
        shortened_url_mock = (
            self.shortened_url_class_mock.get_or_create.return_value
        )
        shorten_url()
        self.assertTrue('requested_alias' in self.session)
        self.assertEqual(
            str(shortened_url_mock.alias),
            self.session['requested_alias']
        )

    def test_redirects_to_the_same_route(self):
        shorten_url()
        self.url_for_mock.assert_called_once_with(shorten_url.__name__)
        redirect_url = self.url_for_mock.return_value
        self.redirect_mock.assert_called_once_with(redirect_url)

    def test_logs_error_on_failure(self):
        """ When register_if_new raises RegistrationRetryLimitExceeeded
        error, shorten_url is expected to log it.
        """
        side_effect = RegistrationRetryLimitExceeded()
        self.register_if_new_mock.side_effect = side_effect

        shorten_url()

        self.app_mock.logger.error.assert_called_once_with(side_effect)

    def test_prepares_failure_message(self):
        """ When register_if_new raises RegistrationRetryLimitExceeeded
        error, shorten_url is expected to prepare a message on the failure.
        The message is expected to include admin email address.
        """
        self.register_if_new_mock.side_effect = RegistrationRetryLimitExceeded
        email = 'admin@urlshortener.com'

        def getitem(index):
            return email if index == 'ADMIN_EMAIL' else None

        self.app_mock.config.__getitem__.side_effect = getitem
        msg_tpl_mock = self.markup_mock.return_value

        shorten_url()

        msg_tpl_mock.format.assert_called_once_with(email)

    def test_flashes_failure_message(self):
        """ When register_if_new raises RegistrationRetryLimitExceeeded
        error, shorten_url is expected to flash a message on the failure
        """
        self.register_if_new_mock.side_effect = RegistrationRetryLimitExceeded
        msg_tpl_mock = self.markup_mock.return_value
        msg_mock = msg_tpl_mock.format.return_value

        shorten_url()

        self.flash_mock.assert_called_once_with(msg_mock, 'error')

    def test_returns_redirect_response(self):
        expected = self.redirect_mock.return_value
        actual = shorten_url()
        self.assertEqual(expected, actual)

    def test_flashes_errors(self):
        errors = [Mock() for _ in range(3)]
        self.form_mock.errors.values.return_value = [errors]
        self.form_mock.validate_on_submit.return_value = False
        shorten_url()
        for i in errors:
            self.flash_mock.assert_any_call(i, 'error')

    def set_up_new_url(self, new_alias='xyz'):
        self.session['requested_alias'] = new_alias
        self.form_mock.validate_on_submit.return_value = False

    def test_fetches_new_url(self):
        """ When session contains alias of a previously generated
        short URL, shorten_url is expected to fetch this URL
        from database
        """
        new_alias = 'xyz'
        self.set_up_new_url(new_alias)

        shorten_url()

        self.shortened_url_class_mock.get.assert_called_once_with(
            new_alias
        )

    def test_prepares_success_message(self):
        """ When session contains alias of a previously generated
        short URL, shorten_url is expected to prepare a
        proper message
        """
        self.set_up_new_url()
        new_url_mock = self.shortened_url_class_mock.get.return_value

        shorten_url()

        self.markup_mock.return_value.format.assert_called_once_with(
            new_url_mock.short_url,
            new_url_mock.preview_url
        )

    def test_flashes_success_message(self):
        """ When session contains alias of a previously generated
        short URL, shorten_url is expected to flash the success message
        """
        self.set_up_new_url()
        message_mock = self.markup_mock.return_value.format.return_value

        shorten_url()

        self.flash_mock.assert_called_once_with(message_mock, 'success')

    def assert_renders_form_template(self):
        shorten_url()
        self.render_template_mock.assert_called_once_with(
            'shorten_url.html',
            form=self.form_mock
        )

    def test_renders_form_template(self):
        self.form_mock.validate_on_submit.return_value = False
        self.assert_renders_form_template()

    def test_renders_form_template_after_shortening_url(self):
        self.set_up_new_url()
        self.assert_renders_form_template()

    def assert_returns_rendered_template(self):
        expected = self.render_template_mock.return_value
        actual = shorten_url()
        self.assertEqual(expected, actual)

    def test_returns_rendered_template(self):
        self.form_mock.validate_on_submit.return_value = False
        self.assert_returns_rendered_template()

    def test_returns_rendered_template_after_shortening_url(self):
        self.set_up_new_url()

        self.assert_returns_rendered_template()


class GetResponseTest(BaseViewTest, unittest.TestCase):
    def setUp(self):
        self.validator_patcher = patch(
            'url_shortener.views.url_validator.get_msg_if_blacklisted'
        )
        self.validator_mock = self.validator_patcher.start()

        self.render_preview_patcher = patch(
            'url_shortener.views.render_preview'
        )
        self.render_preview_mock = self.render_preview_patcher.start()

        self.alternative_action = Mock()

        super(GetResponseTest, self).setUp()

    def tearDown(self):
        self.validator_patcher.stop()
        self.render_preview_patcher.stop()

        super(GetResponseTest, self).tearDown()

    def test_queries_for_alias(self):
        alias = 'xyz'
        get_response(alias, self.alternative_action)
        self.shortened_url_class_mock.get_or_404.assert_called_once_with(alias)

    def test_raises_http_error(self):
        self.shortened_url_class_mock.get_or_404.side_effect = HTTPException
        self.assertRaises(
            HTTPException,
            get_response,
            'xyz',
            self.alternative_action
        )

    def test_validates_url(self):
        get_response('xyz', self.alternative_action)
        shortened_url_mock = (
            self.shortened_url_class_mock.get_or_404.return_value
        )
        self.validator_mock.assert_called_once_with(
            shortened_url_mock.target
        )

    def test_renders_preview_for_invalid_url(self):
        get_response('xyz', self.alternative_action)
        self.render_preview_mock.assert_called_once_with(
            self.shortened_url_class_mock.get_or_404.return_value,
            self.validator_mock.return_value
        )

    def test_returns_preview_for_invalid_url(self):
        expected = self.render_preview_mock.return_value
        actual = get_response('xyz', self.alternative_action)
        self.assertEqual(expected, actual)

    def test_calls_alternative_action_for_valid_url(self):
        self.validator_mock.return_value = None
        function = self.alternative_action
        get_response('xyz', function)
        function.assert_called_once_with(
            self.shortened_url_class_mock.get_or_404.return_value
        )

    def test_returns_result_of_alternative_action(self):
        self.validator_mock.return_value = None
        function = self.alternative_action
        expected = function.return_value
        actual = get_response('xyz', function)
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
