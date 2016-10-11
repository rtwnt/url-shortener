# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock, patch, MagicMock

from werkzeug.exceptions import HTTPException

from url_shortener.views import (
    shorten_url, get_response, URLNotShortenedError
)


class BaseViewTest(object):
    """ A class providing mocks used by all tested view functions """
    def setUp(self):
        self.render_template_patcher = patch(
            'url_shortener.views.render_template'
        )
        self.render_template_mock = self.render_template_patcher.start()

        self.target_url_class_patcher = patch(
            'url_shortener.views.TargetURL'
        )
        self.target_url_class_mock = (
            self.target_url_class_patcher.start()
        )

    def tearDown(self):
        self.render_template_patcher.stop()
        self.target_url_class_patcher.stop()


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

        self.shorten_if_new_patcher = patch(
            'url_shortener.views.shorten_if_new'
        )
        self.shorten_if_new_mock = self.shorten_if_new_patcher.start()

        self.app_patcher = patch('url_shortener.views.app')
        self.app_mock = self.app_patcher.start()
        self.app_mock.config = MagicMock()

        self.markup_patcher = patch('url_shortener.views.Markup')
        self.markup_mock = self.markup_patcher.start()

        self.url_for_patcher = patch('url_shortener.views.url_for')
        self.url_for_mock = self.url_for_patcher.start()

        self.flash_patcher = patch('url_shortener.views.flash')
        self.flash_mock = self.flash_patcher.start()

        super(ShortenURLTest, self).setUp()

    def tearDown(self):
        self.form_class_patcher.stop()
        self.shorten_if_new_patcher.stop()
        self.app_patcher.stop()
        self.markup_patcher.stop()
        self.url_for_patcher.stop()
        self.flash_patcher.stop()

        super(ShortenURLTest, self).tearDown()

    def test_registers_new_short_url(self):
        target_url_mock = (
            self.target_url_class_mock.get_or_create.return_value
        )
        shorten_url()
        self.shorten_if_new_mock.assert_called_once_with(
            target_url_mock,
            self.app_mock.config['ATTEMPT_LIMIT']
        )

    def test_redirects_to_the_same_route(self):
        shorten_url()
        self.url_for_mock.assert_called_once_with(shorten_url.__name__)
        redirect_url = self.url_for_mock.return_value
        self.redirect_mock.assert_called_once_with(redirect_url)

    def test_logs_error_on_failure(self):
        """ When shorten_if_new raises URLNotShortenedError,
        shorten_url is expected to log it.
        """
        side_effect = URLNotShortenedError()
        self.shorten_if_new_mock.side_effect = side_effect

        shorten_url()

        self.app_mock.logger.error.assert_called_once_with(side_effect)

    def test_prepares_failure_message(self):
        """ When shorten_if_new raises URLNotShortenedError,
        shorten_url is expected to prepare a message on the failure.
        The message is expected to include admin email address.
        """
        self.shorten_if_new_mock.side_effect = URLNotShortenedError
        email = 'admin@urlshortener.com'

        def getitem(index):
            return email if index == 'ADMIN_EMAIL' else None

        self.app_mock.config.__getitem__.side_effect = getitem
        msg_tpl_mock = self.markup_mock.return_value

        shorten_url()

        msg_tpl_mock.format.assert_called_once_with(email)

    def test_flashes_failure_message(self):
        """ When shorten_if_new raises URLNotShortenedError,
        shorten_url is expected to flash a message on the failure
        """
        self.shorten_if_new_mock.side_effect = URLNotShortenedError
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

    def test_prepares_success_message(self):
        """ When session contains alias of a previously generated
        short URL, shorten_url is expected to prepare a
        proper message
        """
        url_mock = self.target_url_class_mock.get_or_create.return_value

        shorten_url()

        self.markup_mock.return_value.format.assert_called_once_with(
            url_mock.short_url,
            url_mock.preview_url
        )

    def test_flashes_success_message(self):
        """ When session contains alias of a previously generated
        short URL, shorten_url is expected to flash the success message
        """
        message_mock = self.markup_mock.return_value.format.return_value

        shorten_url()

        self.flash_mock.assert_called_once_with(message_mock, 'success')

    def test_renders_form_template(self):
        self.form_mock.validate_on_submit.return_value = False
        shorten_url()
        self.render_template_mock.assert_called_once_with(
            'shorten_url.html',
            form=self.form_mock
        )

    def test_returns_rendered_template(self):
        self.form_mock.validate_on_submit.return_value = False
        expected = self.render_template_mock.return_value
        actual = shorten_url()
        self.assertEqual(expected, actual)


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
        self.target_url_class_mock.get_or_404.assert_called_once_with(alias)

    def test_raises_http_error(self):
        self.target_url_class_mock.get_or_404.side_effect = HTTPException
        self.assertRaises(
            HTTPException,
            get_response,
            'xyz',
            self.alternative_action
        )

    def test_validates_url(self):
        get_response('xyz', self.alternative_action)
        target_url_mock = (
            self.target_url_class_mock.get_or_404.return_value
        )
        self.validator_mock.assert_called_once_with(
            str(target_url_mock)
        )

    def test_renders_preview_for_invalid_url(self):
        get_response('xyz', self.alternative_action)
        self.render_preview_mock.assert_called_once_with(
            self.target_url_class_mock.get_or_404.return_value,
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
            self.target_url_class_mock.get_or_404.return_value
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
