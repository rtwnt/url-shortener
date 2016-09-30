# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock, patch

from nose_parameterized import parameterized
from sqlalchemy.orm.exc import MultipleResultsFound
from werkzeug.exceptions import HTTPException

from url_shortener.models import (
    Alias, AliasValueError, IntegerAlias, AliasLengthValueError, ShortenedURL,
    IntegrityError, register_if_new, RegistrationRetryLimitExceeded
)


class AliasTest(unittest.TestCase):
    """ Tests for Alias class

    :cvar ALIAS_INTEGER: maps string values of aliases used in tests to
    corresponding integers.
    :cvar INTEGERS: a list of lists, each containing one of the integers
    specified in ALIAS_INTEGER. Used as an argument for
    parameterized.expand()
    :cvar ALIASES_TO_INTEGERS: a list containing tuples, each with a pair of
    alias string and its corresponding integer. Used as an argument for
    parameterized.expand()
    """
    ALIAS_INTEGER = {
        '100': 1*Alias._base**2,
        '221': 2*Alias._base**2+2*Alias._base+1,
        '2020': 2*Alias._base**3+2*Alias._base,
        '222': 2*Alias._base**2+2*Alias._base+2,
        '0': 0,
        Alias._chars[-1]+'00': (Alias._base-1)*Alias._base**2
    }
    INTEGERS = [[v] for v in ALIAS_INTEGER.values()]
    ALIASES_TO_INTEGERS = ALIAS_INTEGER.items()

    def test_init_for_invalid_string(self):
        """ The string contains forbidden characters """
        string = 'ABC'
        self.assertRaises(AliasValueError, Alias, None, string)

    def test_init_for_invalid_arg_set(self):
        """ The arguments integer and string can't both be None """
        self.assertRaises(AliasValueError, Alias, None, None)

    @parameterized.expand(ALIASES_TO_INTEGERS)
    def test_init_for_generated_integer(self, string, expected_integer):
        """ The integer value of alias should be properly calculated
        when integer == None """
        instance = Alias(string=string)
        actual_integer = instance.integer
        self.assertEqual(expected_integer, actual_integer)

    @parameterized.expand(INTEGERS)
    def test_init_for_string_being_none(self, integer):
        """ The string value should not be generated during
        object initialization"""
        instance = Alias(integer=integer)
        self.assertIsNone(instance._string)

    @parameterized.expand(ALIASES_TO_INTEGERS)
    def test_str_for_string_being_none(self, expected_string, integer):
        """ The __str__ method should properly generate string
        based on objects .integer property """
        instance = Alias(integer=integer)
        actual_string = str(instance)
        self.assertEqual(expected_string, actual_string)

    @parameterized.expand([
        ('min_length_less_than_zero', -1, 3),
        ('min_and_max_length_less_than_zero', -3, -2),
        ('max_length_less_than_zero', 1, -1),
        ('max_length_less_than_min', 3, 2),
        ('min_int_of_max_length_larger_than_min_32_int', 3, 10)
    ])
    def test_init_random_factory_for(self, _, min_length, max_length):
        """ Alias.init_random_factory expects two arguments: min_length
        and max_length, referring to minimum and maximum lengths
        for new randomly generated aliases.

        If any of these values is smaller than zero, or if the
        minimum value is larger than the maximum one,
        AliasLengthValueError is expected to be raised
        """
        self.assertRaises(
            AliasLengthValueError,
            Alias.init_random_factory,
            min_length,
            max_length
        )

    @parameterized.expand([
        ('non-equal', 1, 2),
        ('equal', 2, 2),
        ('including_max_allowed_length', 1, Alias._max_allowed_length)
    ])
    def test_init_random_factory_for_args(self, _, min_length, max_length):
        """ For valid arguments, Alias.init_random_factory is expected
        to calculate minimum and maximum integer values for all new
        instances of Alias returned by Alias.create_random, and set
        them to _min_new_int and _max_new_int class attributes,
        respectively.

        The values must fulfill two condtions:
        * Alias._min_new_int <= Alias._max_new_int (obviously)
        * Alias._max_new_int >= Alias._max_int_32
        """
        Alias.init_random_factory(min_length, max_length)
        self.assertTrue(
            hasattr(Alias, '_min_new_int') and hasattr(Alias, '_max_new_int')
        )
        self.assertLessEqual(Alias._min_new_int, Alias._max_new_int)
        self.assertLessEqual(Alias._max_new_int, Alias._max_int_32)


class IntegerAliasTest(unittest.TestCase):
    """ Tests for IntegerAlias class

    :ivar tested_instance: an instance of the class to be tested
    :ivar value: a mock used as value parameter to be passed
    to tested methods
    :ivar dialect: a mock used as dialect parameter to be passed
    to tested methods
    """
    def setUp(self):
        self.tested_instance = IntegerAlias()
        self.value = Mock()
        self.dialect = Mock()
        self.alias_class_patcher = patch('url_shortener.models.Alias')
        self.alias_class_mock = self.alias_class_patcher.start()

    def tearDown(self):
        self.alias_class_patcher.stop()

    @parameterized.expand([
        ['process_bind_param'],
        ['process_literal_param']
    ])
    def test_(self, method_name):
        """ The method should return an integer value of the
        Alias object passed to them as value param
        """
        function = getattr(self.tested_instance, method_name)
        expected = self.value.integer
        actual = function(self.value, self.dialect)
        self.assertEqual(expected, actual)

    def test_process_result_value_creates_alias(self):
        self.tested_instance.process_result_value(
            self.value,
            self.dialect
        )
        self.alias_class_mock.assert_called_once_with(integer=self.value)

    def test_process_result_value_returns_alias(self):
        expected = self.alias_class_mock.return_value
        actual = self.tested_instance.process_result_value(
            self.value,
            self.dialect
        )
        self.assertEqual(expected, actual)


class ShortenedURLTest(unittest.TestCase):
    def setUp(self):
        ModelMock = type('ModelMock', (), {'query': Mock()})
        self.bases_patcher = patch.object(
            ShortenedURL,
            '__bases__',
            (ModelMock,)
        )
        self.bases_patcher.start()
        self.bases_patcher.is_local = True

        self.query_mock = ShortenedURL.query

        self.alias_patcher = patch('url_shortener.models.Alias')
        self.alias_mock = self.alias_patcher.start()

        self.abort_patcher = patch('url_shortener.models.abort')
        self.abort_mock = self.abort_patcher.start()

    def tearDown(self):
        self.bases_patcher.stop()
        self.alias_patcher.stop()
        self.abort_patcher.stop()

    def test_get_or_create_filters_by_target(self):
        target = 'http://xyz.com'
        ShortenedURL.get_or_create(target)
        self.query_mock.filter_by.assert_called_once_with(target=target)

    def test_get_or_create_gets_existing_url(self):
        expected = self.query_mock.filter_by.return_value.one_or_none()
        actual = ShortenedURL.get_or_create('http://xyz.com')
        self.assertEqual(expected, actual)

    def test_get_or_create_creates_new_url(self):
        target = 'http://xyz.com'
        filtered = self.query_mock.filter_by.return_value
        filtered.one_or_none.return_value = None
        expected = target
        actual = ShortenedURL.get_or_create('http://xyz.com').target
        self.assertEqual(expected, actual)

    def test_get_or_create_finds_multiple_urls(self):
        filtered = self.query_mock.filter_by.return_value
        filtered.one_or_none.side_effect = MultipleResultsFound
        self.assertRaises(
            MultipleResultsFound,
            ShortenedURL.get_or_create,
            'http://xyz.com'
        )

    def test_get_or_404_calls_alias_constructor(self):
        alias = 'xyz'
        ShortenedURL.get_or_404(alias)
        self.alias_mock.assert_called_once_with(string=alias)

    def test_get_or_404_queries_database(self):
        valid_alias = self.alias_mock.return_value
        ShortenedURL.get_or_404('xyz')
        self.query_mock.get_or_404.assert_called_once_with(valid_alias)

    def test_get_or_404_gets_existing_url(self):
        expected = self.query_mock.get_or_404.return_value
        actual = ShortenedURL.get_or_404('xyz')
        self.assertEqual(expected, actual)

    def assert_get_or_404_raises_HTTPError(self):
        self.assertRaises(HTTPException, ShortenedURL.get_or_404, 'xyz')

    def test_get_or_404_raises_404_for_invalid_alias(self):
        self.alias_mock.side_effect = AliasValueError
        self.abort_mock.side_effect = HTTPException
        self.assert_get_or_404_raises_HTTPError()
        self.abort_mock.assert_called_once_with(404)

    def test_get_or_404_raises_404_for_not_existing_alias(self):
        self.query_mock.get_or_404.side_effect = HTTPException
        self.assert_get_or_404_raises_HTTPError()


def create_integrity_error():
    return IntegrityError('message', 'statement', ['param_1'], Exception)


class CommitSideEffects():
    """ A class providing side effects for mock of
    db.session.commit function
    """
    def __init__(self, limit):
        self._limit = limit - 1
        self._counter = 0

    def __call__(self):
        if self._counter == self._limit:
            return
        self._counter += 1
        raise create_integrity_error()


class RegisterIfNewTest(unittest.TestCase):
    def setUp(self):
        self.inspect_patcher = patch('url_shortener.models.inspect')
        inspect_mock = self.inspect_patcher.start()
        self.state_mock = inspect_mock.return_value
        self.state_mock.transient = True

        self.db_patcher = patch('url_shortener.models.db')
        self.db_mock = self.db_patcher.start()

        self.app_patcher = patch('url_shortener.models.app')
        self.app_mock = self.app_patcher.start()
        self.limit = 10
        self.app_mock.config = {'REGISTRATION_RETRY_LIMIT': self.limit}

        self.shortened_url = Mock()

    def tearDown(self):
        self.inspect_patcher.stop()
        self.db_patcher.stop()
        self.app_patcher.stop()

    def _call(self):
        register_if_new(self.shortened_url)

    def test_does_nothing_for_not_transient_url(self):
        self.state_mock.transient = False
        self._call()
        self.db_mock.session.add.assert_not_called()
        self.db_mock.session.commit.assert_not_called()

    def test_adds_url_to_db_session(self):
        self._call()
        self.db_mock.session.add.assert_called_once_with(self.shortened_url)

    def test_commits_changes(self):
        self._call()
        self.db_mock.session.commit.assert_called_once_with()

    def _call_for_integrity_error(self):
        self.db_mock.session.commit.side_effect = CommitSideEffects(self.limit)
        self._call()

    def test_rollback_for_integrity_error(self):
        self._call_for_integrity_error()
        self.db_mock.session.rollback.assert_any_call()

    def test_logs_integrity_errors(self):
        self._call_for_integrity_error()
        self.assertTrue(self.app_mock.logger.warning.called)

    def test_for_attempt_limit_exceeded(self):
        self.db_mock.session.commit.side_effect = create_integrity_error()
        self.assertRaises(RegistrationRetryLimitExceeded, self._call)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
