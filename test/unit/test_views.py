# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock, patch

from werkzeug.exceptions import HTTPException

from url_shortener.views import shorten_url, redirect_for, preview


class BaseViewTest(object):
    ''' A class providing mocks used by all tested view functions '''
    def setUp(self):
        self.render_template_patcher = patch(
            'url_shortener.views.render_template'
        )
        self.render_template_mock = self.render_template_patcher.start()

        self.shortened_url_class_patcher = patch(
            'url_shortener.views.ShortenedUrl'
        )
        self.shortened_url_class_mock = (
            self.shortened_url_class_patcher.start()
        )

    def tearDown(self):
        self.render_template_patcher.stop()
        self.shortened_url_class_patcher.stop()


class RedirectPatchMixin(object):
    ''' A mixin providing a mock for flask.redirect function '''
    def setUp(self):
        self.redirect_patcher = patch('url_shortener.views.redirect')
        self.redirect_mock = self.redirect_patcher.start()

        super(RedirectPatchMixin, self).setUp()

    def tearDown(self):
        self.redirect_patcher.stop()

        super(RedirectPatchMixin, self).tearDown()


class ShortenUrlTest(RedirectPatchMixin, BaseViewTest, unittest.TestCase):
    def setUp(self):
        self.form_class_patcher = patch('url_shortener.views.ShortenedUrlForm')
        self.form_class_mock = self.form_class_patcher.start()
        self.form_mock = self.form_class_mock()

        self.register_patcher = patch('url_shortener.views.register')
        self.register_mock = self.register_patcher.start()

        self.url_for_patcher = patch('url_shortener.views.url_for')
        self.url_for_mock = self.url_for_patcher.start()

        self.session_patcher = patch('url_shortener.views.session', {})
        self.session = self.session_patcher.start()

        self.flash_patcher = patch('url_shortener.views.flash')
        self.flash_mock = self.flash_patcher.start()

        super(ShortenUrlTest, self).setUp()

    def tearDown(self):
        self.form_class_patcher.stop()
        self.register_patcher.stop()
        self.url_for_patcher.stop()
        self.session_patcher.stop()
        self.flash_patcher.stop()

        super(ShortenUrlTest, self).tearDown()

    def test_registers_new_short_url(self):
        shortened_url_mock = (
            self.shortened_url_class_mock.get_or_create.return_value
        )
        shorten_url()
        self.register_mock.assert_called_once_with(shortened_url_mock)

    def test_saves_new_alias_in_session(self):
        shortened_url_mock = (
            self.shortened_url_class_mock.get_or_create.return_value
        )
        shorten_url()
        self.assertTrue('new_alias' in self.session)
        self.assertEqual(
            str(shortened_url_mock.alias),
            self.session['new_alias']
        )

    def test_redirects_to_the_same_route(self):
        shorten_url()
        self.url_for_mock.assert_called_once_with(shorten_url.__name__)
        redirect_url = self.url_for_mock.return_value
        self.redirect_mock.assert_called_once_with(redirect_url)

    def test_returns_redirect_response(self):
        expected = self.redirect_mock.return_value
        actual = shorten_url()
        self.assertEqual(expected, actual)

    def test_flashes_errors(self):
        errors = [Mock() for _ in range(3)]
        self.form_mock.url.errors = errors
        self.form_mock.validate_on_submit.return_value = False
        shorten_url()
        for i in errors:
            self.flash_mock.assert_any_call(i, 'error')

    def assert_renders_form_template(self, expected_new_shortened_url):
        shorten_url()
        self.render_template_mock.assert_called_once_with(
            'shorten_url.html',
            form=self.form_mock,
            new_shortened_url=expected_new_shortened_url
        )

    def test_renders_form_template(self):
        self.form_mock.validate_on_submit.return_value = False
        self.assert_renders_form_template(None)

    def test_renders_form_template_after_shortening_url(self):
        self.form_mock.validate_on_submit.return_value = False
        new_alias = 'xyz'
        self.session['new_alias'] = new_alias
        new_shortened_url = (
            self.shortened_url_class_mock.get_or_404.return_value
        )
        self.assert_renders_form_template(new_shortened_url)

    def assert_returns_rendered_template(self):
        expected = self.render_template_mock.return_value
        actual = shorten_url()
        self.assertEqual(expected, actual)

    def test_returns_rendered_template(self):
        self.form_mock.validate_on_submit.return_value = False
        self.assert_returns_rendered_template()

    def test_returns_rendered_template_after_shortening_url(self):
        self.form_mock.validate_on_submit.return_value = False
        new_alias = 'xyz'
        self.session['new_alias'] = new_alias
        self.assert_returns_rendered_template()


class GetOr404CallerTestMixin(object):
    ''' Provides tests for functions that always query for existing
    shortened url using ShortenedUrl.get_or_404 function

    :var function: a function to be tested
    '''
    def test_queries_for_alias(self):
        alias = 'xyz'
        self.function(alias)
        self.shortened_url_class_mock.get_or_404.assert_called_once_with(alias)

    def test_raises_http_error(self):
        self.shortened_url_class_mock.get_or_404.side_effect = HTTPException
        self.assertRaises(HTTPException, self.function, 'xyz')


class RedirectForTest(
        GetOr404CallerTestMixin,
        RedirectPatchMixin,
        BaseViewTest,
        unittest.TestCase):

    function = staticmethod(redirect_for)

    def test_redirects_to_short_url(self):
        shortened_url = self.shortened_url_class_mock.get_or_404.return_value
        self.function('xyz')
        self.redirect_mock.assert_called_once_with(shortened_url.target)

    def test_returns_result_of_redirection(self):
        expected = self.redirect_mock.return_value
        actual = self.function('xyz')
        self.assertEqual(expected, actual)


class PreviewTest(GetOr404CallerTestMixin, BaseViewTest, unittest.TestCase):

    function = staticmethod(preview)

    def test_renders_preview_template(self):
        shortened_url = self.shortened_url_class_mock.get_or_404.return_value
        self.function('xyz')
        self.render_template_mock.assert_called_once_with(
            'preview.html',
            short_url=shortened_url.short_url,
            target=shortened_url.target
        )

    def test_returns_rendered_template(self):
        expected = self.render_template_mock.return_value
        actual = self.function('xyz')
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()