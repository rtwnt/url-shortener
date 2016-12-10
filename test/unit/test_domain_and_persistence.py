# -*- coding: utf-8 -*-

"""Tests for domain and persistence-related classes and functions."""
# pylint: disable=C0103
import unittest
from unittest.mock import Mock, patch, MagicMock

from nose_parameterized import parameterized
from sqlalchemy.orm.exc import MultipleResultsFound

from url_shortener.domain_and_persistence import (
    AliasValueError, AliasLengthValueError, IntegrityError, get_commit_changes,
    AliasAlphabet, AlphabetValueError, CharacterValueError, IntegerAlias,
    BaseTargetURL
)


class AliasAlphabetTest(unittest.TestCase):
    """Tests for AliasAlphabet class.

    :cvar CHARS: value of characters parameter for tested instance
    :cvar MIN_LEN: value of min_length parameter for tested instance
    :cvar MAX_LEN: value of max_length parameter for tested instance
    :cvar tested_instance: instance of AliasAlphabet to be used during tests
    """

    CHARS = '12345acdinrvw'
    MIN_LEN = 2
    MAX_LEN = 6
    tested_instance = AliasAlphabet(CHARS, MIN_LEN, MAX_LEN)

    def setUp(self):
        self.randint_patcher = patch(
            'url_shortener.domain_and_persistence.randint'
        )
        self.randint_mock = self.randint_patcher.start()

        self.choice_patcher = patch(
            'url_shortener.domain_and_persistence.choice'
        )
        self.choice_mock = self.choice_patcher.start()

    def tearDown(self):
        self.randint_patcher.stop()
        self.choice_patcher.stop()

    def test_init_raises_alphabet_value_error(self):
        """Test for expected occurence of AlphabetValueError.

        The constructor is expected to raise AlphabetValueError for
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
        """Test for expected occurence of AliasLengthValueError.

        The constructor is expected to raise AliasLengthValueError
        for min_length and max_length not fulfilling
        0 < min_length <= max_length condition.

        :param min_len: value of min_length parameter of AliasAlphabet
        constructor
        :param max_len: value of max_length parameter of AliasAlphabet
        constructor
        """
        self.assertRaises(
            AliasLengthValueError,
            AliasAlphabet,
            self.CHARS,
            min_len,
            max_len
        )

    def test_from_chars_with_homoglyphs(self):
        """Test value of the instance returned by the factory function.

        The method is expected to create an instance of AliasAlphabet
        only with those characters that are not potentially confusing.
        """
        instance = AliasAlphabet.from_chars_with_homoglyphs(
            self.CHARS + AliasAlphabet.INTAB,
            self.MIN_LEN,
            self.MAX_LEN
        )
        self.assertEqual(self.CHARS, str(instance))

    @parameterized.expand([
        (3, 'cd33d', 'cd3'),
        (4, 'ici23', 'ia2'),
        (5, 'ici4512', 'ia45')
    ])
    def test_create_random_of_length(self, init_len, init_choice, expected):
        """Test create_random method for expected results.

        For initial random lengths and character choices, the method
        is expected to return predictable values.

        :param init_len: initial length value to be provided by the mock
        of the randint function
        :param init_choice: initial choice of characters to be provided
        by the mock of the choice function
        :param expected: a final alias string expected for given values
        to be returned by mocked functions
        """
        self.randint_mock.return_value = init_len
        self.choice_mock.side_effect = init_choice

        actual = self.tested_instance.create_random()

        self.assertEqual(expected, actual)

    def test_create_random_for_first_result_shorter_than_min_length(self):
        """Test the method for generating a long enough alias value.

        If, after elimination of multi-letter homoglyphs, the first
        randomly generated value happens to be shorter than
        pre-configured min_length, the method is expected to create
        another one, until it creates a value of length in
        the configured range.
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
        ('with_homoglyphs_of_both_types', 'cl44', 'd44'),
        ('with_a_homoglyph_replacement_not_in_the_alphabet', 'acrn', 'acrn')
    ])
    def test_from_string(self, _, string, expected):
        """Test return values of the method for given strings.

        For given unsanitized strings, the method is expected to return
        predictable values, with potentially confusig characters
        replaced by their homoglyphs.

        :param string: a string alias that can contain potentially
        confusing characters.
        :param expected: a value of alias expected to be returned
        """
        actual = self.tested_instance.from_string(string)

        self.assertEqual(expected, actual)

    def test_from_string_raises_alias_value_error(self):
        """Test the method for expected occurence of AliasValueError.

        The method is expected to raise AliasValueError if
        the string argument contains characters that are not part of
        the alphabet and are not homoglyphs of characters that are part
        of the alphabet.
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
        """Test return values of the method.

        The method is expected to return index of a character
        included in the alphabet.

        :param char: a character whose index is expected to be returned
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
        """Test for expected occurence of CharacterValueError.

        The method is expected to raise CharacterValueError for
        a character that is not part of the alphabet.

        'Potentially' refers to the possible insertion point for
        the character. For example, 'potentially first' means that if
        the character was added to the alphabet, it would be its first
        character.

        :param char: a character not included in tested alphabet
        instance
        """
        self.assertRaises(
            CharacterValueError,
            self.tested_instance.index,
            char
        )


class IntegerAliasTest(unittest.TestCase):
    """Tests for IntegerAlias class.

    :ivar alphabet_mock: a mock of AliasAlphabet instance to be used
    by tested instance
    :ivar tested_instance: instance of IntegerAlias to be used
    during tests
    """

    def setUp(self):
        self.alphabet_mock = MagicMock()
        """We set the length to 10 so that each digit of integer corresponds
        to a character in string
        """
        self.alphabet_mock.__len__.return_value = 10
        self.alphabet_mock._max_length = 4
        self.tested_instance = IntegerAlias(self.alphabet_mock)

    def test_init_raises_alphabet_value_error(self):
        """Test for expected occurence of AlphabetValueError.

        The constructor is expected to raise AlphabetValueError if
        the alphabet passed to it allows for generating aliases that
        would be converted to integers larger than max int32.
        """
        alphabet_mock = MagicMock()
        alphabet_mock.__len__.return_value = 32
        alphabet_mock._max_length = 10

        self.assertRaises(AlphabetValueError, IntegerAlias, alphabet_mock)

    def test_process_bind_param(self):
        """Test if the method converts a string to an integer."""
        string = 'abxy7'
        self.alphabet_mock.from_string.return_value = string
        expected = 81132
        self.alphabet_mock.index.side_effect = [
            int(i) for i in reversed(str(expected))
        ]
        actual = self.tested_instance.process_bind_param(string, Mock())

        self.assertEqual(expected, actual)

    def test_process_bind_param_raises_alias_value_error(self):
        """Test for expected occurence of AliasValueError.

        The method is expected to raise AliasValueError if
        AliasAlphabet.from_string raises it.
        """
        self.alphabet_mock.from_string.side_effect = AliasValueError
        self.assertRaises(
            AliasValueError,
            self.tested_instance.process_bind_param,
            'abcą',
            Mock()
        )

    def test_process_result_value(self):
        """Test if the method converts an integer to a string."""
        value = 3241
        expected = 'm60x'
        self.alphabet_mock.__getitem__.side_effect = reversed(expected)
        actual = self.tested_instance.process_result_value(value, Mock())
        self.assertEqual(expected, actual)


class BaseTargetURLTest(unittest.TestCase):
    """Tests for BaseTargetURL class.

    :ivar session_mock: a mock of database session to be used by
    tested class
    """

    def setUp(self):
        self.session_mock = MagicMock(spec=['query', 'add', 'no_autoflush'])
        BaseTargetURL._session = self.session_mock

    def tearDown(self):
        BaseTargetURL._session = None

    def test_get_or_create_filters_by_target(self):
        """Test if the method finds a target URL by its value."""
        filter_by_mock = self.session_mock.query.return_value.filter_by
        target = 'http://xyz.com'

        BaseTargetURL.get_or_create(target)

        filter_by_mock.assert_called_once_with(_value=target)

    def test_get_or_create_gets_existing_url_from_db(self):
        """Test if the method returns a value found in database."""
        filtered = self.session_mock.query.return_value.filter_by()
        expected = filtered.one_or_none()
        actual = BaseTargetURL.get_or_create('http://xyz.com')
        self.assertEqual(expected, actual)

    def test_get_or_create_caches_persisted_url(self):
        """Test if a persisted URL is cached for a subsequent call."""
        target = 'http://xyz.com'
        target_url_1 = BaseTargetURL.get_or_create(target)
        query_mock = self.session_mock.query
        called_first_time = query_mock.call_count == 1
        query_mock.reset_mock()

        target_url_2 = BaseTargetURL.get_or_create(target)

        self.assertEqual(target_url_1, target_url_2)
        self.assertTrue(called_first_time)
        self.assertEqual(query_mock.call_count, 0)

    def set_db_query_side_effect(self, side_effect=None):
        """Set up a side effect of a database search.

        :param side_effect: a value to be returned or a class of
        exception to be raised
        """
        filtered = self.session_mock.query.return_value.filter_by()
        func_mock = filtered.one_or_none
        if isinstance(side_effect, type(Exception)):
            func_mock.side_effect = side_effect
        else:
            func_mock.return_value = side_effect

    def test_get_or_create_creates_new_url(self):
        """Test if a new instance of target URL class is created."""
        self.set_db_query_side_effect()
        target = 'http://xyz.com'

        expected = str(BaseTargetURL(target))
        actual = str(BaseTargetURL.get_or_create(target))

        self.assertEqual(str(expected), actual)

    def test_get_or_create_adds_new_url_to_db_session(self):
        """Test if a new target URL is added to database session."""
        self.set_db_query_side_effect()
        target = 'http://xyz.com'

        target_url = BaseTargetURL.get_or_create(target)

        self.session_mock.add.assert_called_once_with(target_url)

    def test_get_or_create_caches_new_url(self):
        """Test if a new URL is cached for a subsequent call."""
        self.set_db_query_side_effect()
        target = 'http://xyz.com'
        target_url_1 = BaseTargetURL.get_or_create(target)
        query_mock = self.session_mock.query
        query_mock.reset_mock()

        target_url_2 = BaseTargetURL.get_or_create(target)

        self.assertEqual(query_mock.call_count, 0)
        self.assertEqual(target_url_1, target_url_2)

    def test_get_or_create_finds_multiple_urls(self):
        """Test if a MutlipleResultsFound error is raised."""
        self.set_db_query_side_effect(MultipleResultsFound)

        self.assertRaises(
            MultipleResultsFound,
            BaseTargetURL.get_or_create,
            'http://xyz.com'
        )


class TestGetCommitChanges(unittest.TestCase):
    """Tests for get_commit_changes function and its return value.

    :cvar LIMIT: a value of INTEGRITY_ERROR_LIMIT option to be set for
    application config mock
    :cvar TEST_PARAMS: a list of parameter tuples to be used for
    testing. Each tuple contains:
        * a string to be added to test function name
        * a number of integrity errors to occur during a test
    :ivar app_mock: a mock of Flask application object to be used
    by the tested function
    :ivar logger_mock: a mock of a logger instance to be used by
    the tested function
    :ivar commit_changes: a function to be tested - a return value
    of get_commit_changes
    """

    LIMIT = 10
    TEST_PARAMS = [
        ('no_integrity_errors', 0),
        ('one_integrity_error', 1),
        ('two_integrity_errors', 2),
        ('too_many_integrity_errors', LIMIT + 1)
    ]

    def setUp(self):
        db_mock = Mock()
        self.session_mock = db_mock.session

        app_mock = Mock()
        app_mock.config = {}
        app_mock.config['INTEGRITY_ERROR_LIMIT'] = self.LIMIT
        self.logger_mock = app_mock.logger.warning

        self.commit_changes = get_commit_changes(app_mock, db_mock)

    def _call(self, integrity_error_count):
        """Call the tested function.

        :param integrity_error_count: a number of integrity errors to
        be raised by database session commit method.
        """
        error = IntegrityError('message', 'statement', ['param_1'], Exception)
        self.session_mock.commit.side_effect = (
            [error] * integrity_error_count + [None]
        )

        self.commit_changes()

    @parameterized.expand(TEST_PARAMS)
    def test_commits_pending_changes_with(self, _, integrity_error_count):
        """Test if the function commits pending changes.

        :param integrity_error_count: a number of integrity errors to
        be raised by database session commit method.
        """
        self._call(integrity_error_count)

        self.assertEqual(
            self.session_mock.commit.call_count,
            integrity_error_count + 1
        )

    @parameterized.expand(TEST_PARAMS)
    def test_rolls_back_for(self, _, integrity_error_count):
        """Test if the changes are rolled back when error occurs.

        :param integrity_error_count: a number of integrity errors to
        be raised by database session commit method.
        """
        self._call(integrity_error_count)

        self.assertEqual(
            self.session_mock.rollback.call_count,
            integrity_error_count
        )

    def test_does_not_log_warning(self):
        """Test if warnings are not logged.

        Warnings are not expected to be logged until the limit of
        integrity errors is reached.
        """
        for integrity_error_count in range(self.LIMIT + 1):
            self._call(integrity_error_count)

            self.assertEqual(self.logger_mock.call_count, 0)

    def test_logs_warning(self):
        """Test if warnings are logged.

        Warnings are expected to be logged after the limit of integrity
        errors is exceeded.
        """
        self._call(self.LIMIT + 1)

        self.assertTrue(self.logger_mock.called)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
