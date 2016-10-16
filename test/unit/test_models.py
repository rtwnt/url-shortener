# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock, patch

from nose_parameterized import parameterized
from sqlalchemy.orm.exc import MultipleResultsFound
from werkzeug.exceptions import HTTPException

from url_shortener.models import (
    Alias, AliasValueError, IntegerAlias, AliasLengthValueError, TargetURL,
    IntegrityError, commit_changes, AliasAlphabet, AlphabetValueError,
    CharacterValueError
)


class AliasAlphabetTest(unittest.TestCase):
    """Tests for AliasAlphabet class

    :cvar CHARS: value of characters parameter for tested instance
    :cvar MIN_LEN: value of min_length parameter for tested instance
    :cvar MAX_LEN: value of max_length parameter for tested instance
    :cvar tested_instance: instance of AliasAlphabet to be used during tests
    """

    CHARS = '12345acdivw'
    MIN_LEN = 2
    MAX_LEN = 6
    tested_instance = AliasAlphabet(CHARS, MIN_LEN, MAX_LEN)

    def setUp(self):
        self.randint_patcher = patch('url_shortener.models.randint')
        self.randint_mock = self.randint_patcher.start()

        self.choice_patcher = patch('url_shortener.models.choice')
        self.choice_mock = self.choice_patcher.start()

        self.tested_instance = AliasAlphabet(
            self.CHARS,
            self.MIN_LEN,
            self.MAX_LEN
        )

    def tearDown(self):
        self.randint_patcher.stop()
        self.choice_patcher.stop()

    def test_init_raises_alphabet_value_error(self):
        """The constructor is expected to raise AlphabetValueError for
        a characters argument that includes potentially confusing
        characters.
        """
        chars = self.CHARS + AliasAlphabet.INTAB
        self.assertRaises(AlphabetValueError, AliasAlphabet, chars, 2, 4)

    @parameterized.expand([
        ('min > max', 5, 4),
        ('min = 0', 0, 4),
        ('min < 0', -2, 4),
    ])
    def test_init_raises_alias_length_value_error(self, _, min_len, max_len):
        """The constructor is expected to raise AliasLengthValueError
        for min_length and max_length not fuilfilling
        0 < min_length <= max_length condition
        """
        self.assertRaises(
            AliasLengthValueError,
            AliasAlphabet,
            self.CHARS,
            min_len,
            max_len
        )

    def test_from_chars_with_homoglyphs(self):
        """The method is expected to create instance of AliasAlphabet
        only with those characters that are not potentially confusing
        """
        instance = AliasAlphabet.from_chars_with_homoglyphs(
            self.CHARS + AliasAlphabet.INTAB,
            self.MIN_LEN,
            self.MAX_LEN
        )
        self.assertEqual(self.CHARS, instance._characters)

    @parameterized.expand([
        (3, 'cd33d', 'cd3'),
        (4, 'ici23', 'ia2'),
        (5, 'ici4512', 'ia45')
    ])
    def test_create_random_of_length(self, init_len, init_choice, expected):
        """For initial random lengths and character choices, the method
        is expected to return predictable values
        """
        self.randint_mock.return_value = init_len
        self.choice_mock.side_effect = init_choice

        actual = self.tested_instance.create_random()

        self.assertEqual(expected, actual)

    def test_create_random_for_first_result_shorter_than_min_length(self):
        """If, after elimination of multi-letter homoglyphs, the first
        randomly generated value happens to be shorter than
        pre-configured min_length, the method is expected to create
        another one, until it creates a value of length in
        the configured range
        """
        self.randint_mock.side_effect = self.MIN_LEN, self.MIN_LEN + 1
        self.choice_mock.side_effect = 'civv4'
        expected = 'w4'

        actual = self.tested_instance.create_random()

        self.assertEqual(expected, actual)

    @parameterized.expand([
        ('', 'acd12', 'acd12'),
        ('with_homoglyphs', 'al23', 'a123'),
        ('with_multiletter_homoglyphs', 'ac144', 'ad44'),
        ('with_homoglyphs_of_both_types', 'lc144', '1d44'),
        ('with_homoglyphs_of_both_types', 'cl44', 'd44')
    ])
    def test_from_string(self, _, string, expected):
        """For given strings, the method is expected to return
        predictable values, with potentially confusig characters
        replaced by their homoglyphs
        """
        actual = self.tested_instance.from_string(string)

        self.assertEqual(expected, actual)

    def test_from_string_raises_alias_value_error(self):
        """The method is expected to raise AliasValueError if
        the string argument contains characters that are not part of
        the alphabet and are not homoglyphs of characters that are part
        of the alphabet
        """
        self.assertRaises(
            AliasValueError,
            self.tested_instance.from_string,
            'xyz'
        )

    @parameterized.expand([
        ('first_character', '1'),
        ('medial_character', 'a'),
        ('last_character', 'w'),
    ])
    def test_index_for(self, _, char):
        """The method is expected to return index of a character
        included in the alphabet
        """
        expected = self.CHARS.index(char)
        actual = self.tested_instance.index(char)

        self.assertEqual(expected, actual)

    @parameterized.expand([
        ('first_character', '+'),
        ('medial_character', 'b'),
        ('final_character', 'z')
    ])
    def test_index_raises_error_for_potentially(self, _, char):
        """The method is expected to raise CharacterValueError for
        a character that is not part of the alphabet

        'Potentially' refers to the possible insertion point for
        the character. For example, 'potentially first' means that if
        the character was added to the alphabet, it would be its first
        character.
        """
        self.assertRaises(
            CharacterValueError,
            self.tested_instance.index,
            char
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


class TestCommitChanges(unittest.TestCase):
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
        error = IntegrityError('message', 'statement', ['param_1'], Exception)
        self.session_mock.commit.side_effect = (
            [error] * integrity_error_count + [None]
        )

        commit_changes()

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
