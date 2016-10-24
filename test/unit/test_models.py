# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock, patch, MagicMock

from nose_parameterized import parameterized
from sqlalchemy.orm.exc import MultipleResultsFound

from url_shortener.models import (
    AliasValueError, AliasLengthValueError, IntegrityError, commit_changes,
    AliasAlphabet, AlphabetValueError, CharacterValueError, IntegerAlias,
    BaseTargetURL
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


class IntegerAliasTest(unittest.TestCase):
    def setUp(self):
        self.alphabet_mock = MagicMock()
        """We set the length to 10 so that each digit of integer corresponds
        to a character in string
        """
        self.alphabet_length = 10
        self.alphabet_mock.__len__.return_value = self.alphabet_length
        self.alphabet_mock._max_length = 4
        self.tested_instance = IntegerAlias(self.alphabet_mock)

    def test_init_raises_alphabet_value_error(self):
        """The constructor is expected to raise AlphabetValueError if
        the alphabet passed to it allows for generating aliases that
        would be converted to integers larger than max int32
        """
        alphabet_mock = MagicMock()
        alphabet_mock.__len__.return_value = 32
        alphabet_mock._max_length = 10

        self.assertRaises(AlphabetValueError, IntegerAlias, alphabet_mock)

    def test_process_bind_param(self):
        """The method is expected to convert a string to an integer"""
        string = 'abxy7'
        self.alphabet_mock.from_string.return_value = string
        expected = 81132
        self.alphabet_mock.index.side_effect = [
            int(i) for i in reversed(str(expected))
        ]
        actual = self.tested_instance.process_bind_param(string, Mock())

        self.assertEqual(expected, actual)

    def test_process_bind_param_raises_alias_value_error(self):
        """The method is expected to raise AliasValueError if
        AliasAlphabet.from_string raises it
        """
        self.alphabet_mock.from_string.side_effect = AliasValueError
        self.assertRaises(
            AliasValueError,
            self.tested_instance.process_bind_param,
            'abcą',
            Mock()
        )

    def test_process_result_value(self):
        """The method is expected to convert an integer to a string"""
        value = 3241
        expected = 'm60x'
        self.alphabet_mock.__getitem__.side_effect = reversed(expected)
        actual = self.tested_instance.process_result_value(value, Mock())
        self.assertEqual(expected, actual)


class BaseTargetURLTest(unittest.TestCase):

    class_under_test = BaseTargetURL

    def setUp(self):
        self.session_mock = MagicMock(spec=['query', 'add', 'no_autoflush'])
        BaseTargetURL._session = self.session_mock

    def tearDown(self):
        delattr(BaseTargetURL, '_session')

    def test_get_or_create_filters_by_target(self):
        filter_by_mock = self.session_mock.query.return_value.filter_by
        target = 'http://xyz.com'

        self.class_under_test.get_or_create(target)

        filter_by_mock.assert_called_once_with(_value=target)

    def test_get_or_create_gets_existing_url_from_db(self):
        filtered = self.session_mock.query.return_value.filter_by()
        expected = filtered.one_or_none()
        actual = self.class_under_test.get_or_create('http://xyz.com')
        self.assertEqual(expected, actual)

    def test_get_or_create_caches_persisted_url(self):
        target = 'http://xyz.com'
        target_url_1 = self.class_under_test.get_or_create(target)
        query_mock = self.session_mock.query
        called_first_time = query_mock.call_count == 1
        query_mock.reset_mock()

        target_url_2 = self.class_under_test.get_or_create(target)

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

        expected = str(self.class_under_test(target))
        actual = str(self.class_under_test.get_or_create(target))

        self.assertEqual(str(expected), actual)

    def test_get_or_create_adds_new_url_to_db_session(self):
        self.set_db_query_side_effect()
        target = 'http://xyz.com'

        target_url = self.class_under_test.get_or_create(target)

        self.session_mock.add.assert_called_once_with(target_url)

    def test_get_or_create_caches_new_url(self):
        self.set_db_query_side_effect()
        target = 'http://xyz.com'
        target_url_1 = self.class_under_test.get_or_create(target)
        query_mock = self.session_mock.query
        query_mock.reset_mock()

        target_url_2 = self.class_under_test.get_or_create(target)

        self.assertEqual(query_mock.call_count, 0)
        self.assertEqual(target_url_1, target_url_2)

    def test_get_or_create_finds_multiple_urls(self):
        self.set_db_query_side_effect(MultipleResultsFound)

        self.assertRaises(
            MultipleResultsFound,
            self.class_under_test.get_or_create,
            'http://xyz.com'
        )


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
