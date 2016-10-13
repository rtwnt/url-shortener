# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock, patch

from nose_parameterized import parameterized
from sqlalchemy.orm.exc import MultipleResultsFound
from werkzeug.exceptions import HTTPException

from url_shortener.models import (
    Alias, AliasValueError, IntegerAlias, AliasLengthValueError, TargetURL,
    IntegrityError, shorten_if_new, URLNotShortenedError,
    commit_changes_to_database
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

    :ivar alias_class_patcher: an object used to patch Alias
    class object used by tested methods
    :ivar alias_class_mock: a mock of Alias class object to
    be used during testing
    :ivar tested_instance: an instance of the class to be tested
    """
    def setUp(self):
        self.alias_class_patcher = patch('url_shortener.models.Alias')
        self.alias_class_mock = self.alias_class_patcher.start()

        self.tested_instance = IntegerAlias()

    def tearDown(self):
        self.alias_class_patcher.stop()

    def call(self, method_name, value=Mock()):
        function = getattr(self.tested_instance, method_name)
        return function(value, Mock())

    @parameterized.expand([
        ('process_bind_param'),
        ('process_literal_param')
    ])
    def test_getting_integer_with(self, function_name):
        value = Mock()
        expected = value.integer
        actual = self.call(function_name, value)

        self.assertEqual(expected, actual)

    def test_process_result_value_creates_alias(self):
        value = Mock()
        self.call('process_result_value', value)

        self.alias_class_mock.assert_called_once_with(integer=value)

    def test_process_result_value_returns_alias(self):
        actual = self.call('process_result_value')
        expected = self.alias_class_mock.return_value

        self.assertEqual(expected, actual)


class TargetURLTest(unittest.TestCase):
    def setUp(self):
        ModelMock = type('ModelMock', (), {'query': Mock()})
        self.bases_patcher = patch.object(
            TargetURL,
            '__bases__',
            (ModelMock,)
        )
        self.bases_patcher.start()
        self.bases_patcher.is_local = True

        self.query_mock = TargetURL.query

        self.alias_patcher = patch('url_shortener.models.Alias')
        self.alias_mock = self.alias_patcher.start()

        self.session_patcher = patch(
            'url_shortener.models.db.session',
            spec=['query', 'add', 'no_autoflush']
        )
        self.session_mock = self.session_patcher.start()

    def tearDown(self):
        self.bases_patcher.stop()
        self.alias_patcher.stop()
        self.session_patcher.stop()

    def test_get_creates_alias(self):
        alias = 'abc'
        TargetURL.get(alias)
        self.alias_mock.assert_called_once_with(string=alias)

    def test_get_queries_for_alias(self):
        TargetURL.get('abc')
        self.query_mock.get.assert_called_once_with(
            self.alias_mock.return_value
        )

    def test_get_returns_query_result(self):
        expected = self.query_mock.get.return_value
        actual = TargetURL.get('abc')
        self.assertEqual(expected, actual)

    def test_get_or_create_filters_by_target(self):
        filter_by_mock = self.session_mock.query.return_value.filter_by
        target = 'http://xyz.com'

        TargetURL.get_or_create(target)

        filter_by_mock.assert_called_once_with(_value=target)

    def test_get_or_create_gets_existing_url_from_db(self):
        filtered = self.session_mock.query.return_value.filter_by()
        expected = filtered.one_or_none()
        actual = TargetURL.get_or_create('http://xyz.com')
        self.assertEqual(expected, actual)

    def test_get_or_create_caches_persisted_url(self):
        target = 'http://xyz.com'
        target_url_1 = TargetURL.get_or_create(target)
        query_mock = self.session_mock.query
        called_first_time = query_mock.call_count == 1
        query_mock.reset_mock()

        target_url_2 = TargetURL.get_or_create(target)

        self.assertEqual(target_url_1, target_url_2)
        self.assertTrue(called_first_time)
        self.assertEqual(query_mock.call_count, 0)

    def set_db_query_side_effect(self, side_effect=None):
        filtered = self.session_mock.query.return_value.filter_by()
        func_mock = filtered.one_or_none
        if isinstance(side_effect, type(Exception)):
            func_mock.side_effect = side_effect
        else:
            func_mock.return_value = side_effect

    def test_get_or_create_creates_new_url(self):
        self.set_db_query_side_effect()
        target = 'http://xyz.com'

        expected = str(TargetURL(target))
        actual = str(TargetURL.get_or_create(target))

        self.assertEqual(str(expected), actual)

    def test_get_or_create_adds_new_url_to_db_session(self):
        self.set_db_query_side_effect()
        target = 'http://xyz.com'

        target_url = TargetURL.get_or_create(target)

        self.session_mock.add.assert_called_once_with(target_url)

    def test_get_or_create_caches_new_url(self):
        self.set_db_query_side_effect()
        target = 'http://xyz.com'
        target_url_1 = TargetURL.get_or_create(target)
        query_mock = self.session_mock.query
        query_mock.reset_mock()

        target_url_2 = TargetURL.get_or_create(target)

        self.assertEqual(query_mock.call_count, 0)
        self.assertEqual(target_url_1, target_url_2)

    def test_get_or_create_finds_multiple_urls(self):
        self.set_db_query_side_effect(MultipleResultsFound)

        self.assertRaises(
            MultipleResultsFound,
            TargetURL.get_or_create,
            'http://xyz.com'
        )

    def test_get_or_404_calls_alias_constructor(self):
        alias = 'xyz'
        TargetURL.get_or_404(alias)
        self.alias_mock.assert_called_once_with(string=alias)

    def test_get_or_404_queries_database(self):
        valid_alias = self.alias_mock.return_value
        TargetURL.get_or_404('xyz')
        self.query_mock.get_or_404.assert_called_once_with(valid_alias)

    def test_get_or_404_gets_existing_url(self):
        expected = self.query_mock.get_or_404.return_value
        actual = TargetURL.get_or_404('xyz')
        self.assertEqual(expected, actual)

    def assert_get_or_404_raises_HTTPError(self):
        self.assertRaises(HTTPException, TargetURL.get_or_404, 'xyz')

    def test_get_or_404_raises_404_for_not_existing_alias(self):
        self.query_mock.get_or_404.side_effect = HTTPException
        self.assert_get_or_404_raises_HTTPError()


def create_integrity_error():
    return IntegrityError('message', 'statement', ['param_1'], Exception)


def commit_side_effects(integrity_error_count):
    error = create_integrity_error()
    return [error] * integrity_error_count + [None]


class ShortenIfNewTest(unittest.TestCase):
    def setUp(self):
        self.inspect_patcher = patch('url_shortener.models.inspect')
        inspect_mock = self.inspect_patcher.start()
        self.state_mock = inspect_mock.return_value
        self.state_mock.transient = True

        self.db_patcher = patch('url_shortener.models.db')
        self.db_mock = self.db_patcher.start()

        self.limit = 10

        self.target_url = Mock()

    def tearDown(self):
        self.inspect_patcher.stop()
        self.db_patcher.stop()

    def _call(self):
        shorten_if_new(self.target_url, self.limit)

    def test_does_nothing_for_not_transient_url(self):
        self.state_mock.transient = False
        self._call()
        self.assertEqual(self.db_mock.session.add.call_count, 0)
        self.assertEqual(self.db_mock.session.commit.call_count, 0)

    def test_adds_url_to_db_session(self):
        self._call()
        self.db_mock.session.add.assert_called_once_with(self.target_url)

    def test_commits_changes(self):
        self._call()
        self.db_mock.session.commit.assert_called_once_with()

    def _call_for_integrity_error(self):
        self.db_mock.session.commit.side_effect = commit_side_effects(
            self.limit - 1
        )
        self._call()

    def test_adds_url_to_db_session_for_integrity_error(self):
        self._call_for_integrity_error()
        self.assertEqual(self.db_mock.session.add.call_count, self.limit)
        self.db_mock.session.add.assert_called_with(self.target_url)

    def test_commits_changes_for_integrity_error(self):
        self._call_for_integrity_error()
        self.assertEqual(self.db_mock.session.commit.call_count, self.limit)

    def test_rollback_for_integrity_error(self):
        self._call_for_integrity_error()
        self.assertEqual(
            self.db_mock.session.rollback.call_count,
            self.limit - 1
        )

    def test_for_shortening_failure(self):
        self.db_mock.session.commit.side_effect = create_integrity_error()
        self.assertRaises(URLNotShortenedError, self._call)


class TestCommitChangesToDatabase(unittest.TestCase):
    LIMIT = 10
    TEST_PARAMS = [
        ('no_integrity_errors', 0),
        ('one_integrity_error', 1),
        ('two_integrity_errors', 2),
        ('too_many_integrity_errors', LIMIT + 1)
    ]

    def setUp(self):
        self.session_patcher = patch('url_shortener.models.db.session')
        self.session_mock = self.session_patcher.start()

        self.current_app_patcher = patch('url_shortener.models.current_app')
        current_app_mock = self.current_app_patcher.start()
        current_app_mock.config = {}
        current_app_mock.config['INTEGRITY_ERROR_LIMIT'] = self.LIMIT
        self.logger_mock = current_app_mock.logger.warning

    def tearDown(self):
        self.session_mock.stop()
        self.current_app_patcher.stop()

    def _call(self, integrity_error_count):
        self.session_mock.commit.side_effect = commit_side_effects(
            integrity_error_count
        )

        commit_changes_to_database()

    @parameterized.expand(TEST_PARAMS)
    def test_commits_pending_changes_with(self, _, integrity_error_count):
        self._call(integrity_error_count)

        self.assertEqual(
            self.session_mock.commit.call_count,
            integrity_error_count + 1
        )

    @parameterized.expand(TEST_PARAMS)
    def test_rolls_back_for(self, _, integrity_error_count):
        self._call(integrity_error_count)

        self.assertEqual(
            self.session_mock.rollback.call_count,
            integrity_error_count
        )

    def test_does_not_log_warning(self):
        for integrity_error_count in range(self.LIMIT + 1):
            self._call(integrity_error_count)

            self.assertEqual(self.logger_mock.call_count, 0)

    def test_logs_warning(self):
        self._call(self.LIMIT + 1)

        self.assertTrue(self.logger_mock.called)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
