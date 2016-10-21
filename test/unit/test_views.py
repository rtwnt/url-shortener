# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock, patch, MagicMock

from werkzeug.exceptions import HTTPException

from url_shortener.views import shorten_url, get_response


class BaseViewTest(object):
    """ A class providing mocks used by all tested view functions """
    def setUp(self):
        self.render_template_patcher = patch(
            'url_shortener.views.render_template'
        )
        self.render_template_mock = self.render_template_patcher.start()

        self.target_url_class_mock = Mock()

    def tearDown(self):
        self.render_template_patcher.stop()


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
        self.form_class_mock = Mock()
        self.form_mock = self.form_class_mock()
        self.form_mock.errors.values = MagicMock()

        self.commit_changes_patcher = patch(
            'url_shortener.views.commit_changes'
        )
        self.commit_changes_mock = self.commit_changes_patcher.start()

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
        self.commit_changes_patcher.stop()
        self.app_patcher.stop()
        self.markup_patcher.stop()
        self.url_for_patcher.stop()
        self.flash_patcher.stop()

        super(ShortenURLTest, self).tearDown()

    def _call(self):
        return shorten_url(self.target_url_class_mock, self.form_class_mock)

    def test_registers_new_short_url(self):
        self._call()
        self.assertTrue(self.commit_changes_mock.called)

    def test_redirects_to_the_same_route(self):
        self._call()
        self.url_for_mock.assert_called_once_with(shorten_url.__name__)
        redirect_url = self.url_for_mock.return_value
        self.redirect_mock.assert_called_once_with(redirect_url)

    def test_returns_redirect_response(self):
        expected = self.redirect_mock.return_value
        actual = self._call()
        self.assertEqual(expected, actual)

    def test_flashes_errors(self):
        errors = [Mock() for _ in range(3)]
        self.form_mock.errors.values.return_value = [errors]
        self.form_mock.validate_on_submit.return_value = False
        self._call()
        for i in errors:
            self.flash_mock.assert_any_call(i, 'error')

    def test_prepares_success_message(self):
        """ When session contains alias of a previously generated
        short URL, shorten_url is expected to prepare a
        proper message
        """
        url_mock = self.target_url_class_mock.get_or_create.return_value

        self._call()

        self.markup_mock.return_value.format.assert_called_once_with(
            url_mock.short_url,
            url_mock.preview_url
        )

    def test_flashes_success_message(self):
        """ When session contains alias of a previously generated
        short URL, shorten_url is expected to flash the success message
        """
        message_mock = self.markup_mock.return_value.format.return_value

        self._call()

        self.flash_mock.assert_called_once_with(message_mock, 'success')

    def test_renders_form_template(self):
        self.form_mock.validate_on_submit.return_value = False
        self._call()
        self.render_template_mock.assert_called_once_with(
            'shorten_url.html',
            form=self.form_mock
        )

    def test_returns_rendered_template(self):
        self.form_mock.validate_on_submit.return_value = False
        expected = self.render_template_mock.return_value
        actual = self._call()
        self.assertEqual(expected, actual)


class GetResponseTest(BaseViewTest, unittest.TestCase):
    def setUp(self):
        self.validator_obj_mock = Mock()
        self.validator_mock = self.validator_obj_mock.get_msg_if_blacklisted

        self.render_preview_patcher = patch(
            'url_shortener.views.render_preview'
        )
        self.render_preview_mock = self.render_preview_patcher.start()

        self.alternative_action = Mock()

        super(GetResponseTest, self).setUp()

    def tearDown(self):
        self.render_preview_patcher.stop()

        super(GetResponseTest, self).tearDown()

    def _call(self, alias):
        return get_response(
            alias,
            self.alternative_action,
            self.target_url_class_mock,
            self.validator_obj_mock
        )

    def test_queries_for_alias(self):
        alias = 'xyz'
        self._call(alias)
        self.target_url_class_mock.query.get_or_404.assert_called_once_with(
            alias
        )

    def test_raises_http_error(self):
        self.target_url_class_mock.query.get_or_404.side_effect = HTTPException
        self.assertRaises(
            HTTPException,
            self._call,
            'xyz',
        )

    def test_validates_url(self):
        self._call('xyz')
        target_url_mock = (
            self.target_url_class_mock.query.get_or_404.return_value
        )
        self.validator_mock.assert_called_once_with(
            str(target_url_mock)
        )

    def test_renders_preview_for_invalid_url(self):
        self._call('xyz')
        self.render_preview_mock.assert_called_once_with(
            self.target_url_class_mock.query.get_or_404.return_value,
            self.validator_mock.return_value
        )

    def test_returns_preview_for_invalid_url(self):
        expected = self.render_preview_mock.return_value
        actual = self._call('xyz')
        self.assertEqual(expected, actual)

    def test_calls_alternative_action_for_valid_url(self):
        self.validator_mock.return_value = None
        self._call('xyz')
        self.alternative_action.assert_called_once_with(
            self.target_url_class_mock.query.get_or_404.return_value
        )

    def test_returns_result_of_alternative_action(self):
        self.validator_mock.return_value = None
        expected = self.alternative_action.return_value
        actual = self._call('xyz')
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
