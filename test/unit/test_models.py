# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock, patch

from nose_parameterized import parameterized
from sqlalchemy.orm.exc import MultipleResultsFound

from url_shortener.models import (
    Alias, AliasValueError, IntegerAlias, AliasLengthValueError, NumeralSystem,
    NumeralValueError, ShortenedUrl
)


class NumeralSystemTest(unittest.TestCase):
    ''' Tests for NumeralSystem class

    :var BINARY: instance of NumeralSystem representing binary
    numeral system
    :var DECIMAL: instance of NumeralSystem representing decimal
    numeral system
    :var TWO_DIGIT_BINARY: a list containing name of a test, binary
    numeral system object and integer for length parameter. Used for
    testing get_min_value and get_max_value methods.
    :var THREE_DIGIT_DECIMAL: a list containing name of a test, decimal
    numeral system object and integer for length parameter. Used for
    testing get_min_value and get_max_value methods.
    :var CONVERSION_PARAMS: a list containing tuples, each with a name
    of a test, instance of NumeralSystem to be used in test, an integer
    and its corresponding value as a number written in the system. Used
    for testing to_string and to_integer methods.
    '''
    BINARY = NumeralSystem('01')
    DECIMAL = NumeralSystem('0123456789')
    TWO_DIGIT_BINARY = ['two_digit_binary', BINARY, 2]
    THREE_DIGIT_DECIMAL = ['three_digit_decimal', DECIMAL, 3]
    CONVERSION_PARAMS = [
        ('binary', BINARY, 3, '11'),
        ('decimal', DECIMAL, 123, '123')
    ]

    @parameterized.expand(CONVERSION_PARAMS)
    def test_to_string_from(self, _, system, integer, expected):
        actual = system.to_string(integer)
        self.assertEqual(expected, actual)

    @parameterized.expand(CONVERSION_PARAMS)
    def test_to_integer_from(self, _, system, expected, string):
        actual = system.to_integer(string)
        self.assertEqual(expected, actual)

    @parameterized.expand([
        ('binary', BINARY, '123'),
        ('decimal', DECIMAL, '99A')
    ])
    def test_to_integer_from_invalid(self, _, system, string):
        self.assertRaises(NumeralValueError, system.to_integer, string)

    @parameterized.expand([
        TWO_DIGIT_BINARY + [2],
        THREE_DIGIT_DECIMAL + [100],
    ])
    def test_get_min_value_of_(self, _, system, length, expected):
        self.assertEqual(expected, system.get_min_value(length))

    @parameterized.expand([
        TWO_DIGIT_BINARY + [3],
        THREE_DIGIT_DECIMAL + [999],
    ])
    def test_get_max_value_of_(self, _, system, length, expected):
        self.assertEqual(expected, system.get_max_value(length))


class AliasTest(unittest.TestCase):
    ''' Tests for Alias class

    :var ALIAS_INTEGER: maps string values of aliases used in tests to
    corresponding integers.
    :var INTEGERS: a list of lists, each containing one of the integers
    specified in ALIAS_INTEGER. Used as an argument for
    parameterized.expand()
    :var ALIASES_TO_INTEGERS: a list containing tuples, each with a pair of
    alias string and its corresponding integer. Used as an argument for
    parameterized.expand()
    '''
    ALIAS_INTEGER = {
        'baa': 1*3**2,
        'ccb': 2*3**2+2*3+1,
        'caca': 2*3**3+2*3,
        'ccc': 2*3**2+2*3+2,
        'a': 0
    }
    INTEGERS = [[v] for v in ALIAS_INTEGER.values()]
    ALIASES_TO_INTEGERS = ALIAS_INTEGER.items()

    def setUp(self):
        self.numeral_system = Mock()

        def to_integer(string):
            try:
                return self.ALIAS_INTEGER[string]
            except KeyError:
                raise NumeralValueError

        self.numeral_system.to_integer.side_effect = to_integer

        def to_string(integer):
            for alias, i in self.ALIASES_TO_INTEGERS:
                if i == integer:
                    return alias
        self.numeral_system.to_string.side_effect = to_string
        Alias._SYSTEM = self.numeral_system

    def test_init_for_invalid_string(self):
        ''' The string contains forbidden characters '''
        string = 'abcd'
        self.assertRaises(AliasValueError, Alias, None, string)

    def test_init_for_invalid_arg_set(self):
        ''' The arguments integer and string can't both be None '''
        self.assertRaises(AliasValueError, Alias, None, None)

    @parameterized.expand(ALIASES_TO_INTEGERS)
    def test_init_for_generated_integer(self, string, expected_integer):
        ''' The integer value of alias should be properly calculated
        when integer == None '''
        instance = Alias(string=string)
        actual_integer = instance.integer
        self.assertEqual(expected_integer, actual_integer)

    @parameterized.expand(INTEGERS)
    def test_init_for_string_being_none(self, integer):
        ''' The string value should not be generated during
        object initialization'''
        instance = Alias(integer=integer)
        self.assertIsNone(instance._string)

    @parameterized.expand(ALIASES_TO_INTEGERS)
    def test_str_for_string_being_none(self, expected_string, integer):
        ''' The __str__ method should properly generate string
        based on objects .integer property '''
        instance = Alias(integer=integer)
        actual_string = str(instance)
        self.assertEqual(expected_string, actual_string)

    @parameterized.expand([
        ('min_length_less_than_zero', -1, 3),
        ('min_and_max_length_less_than_zero', -3, -2),
        ('max_length_less_than_zero', 1, -1),
        ('max_length_less_than_min', 3, 2)
    ])
    def test_random_factory_for(self, _, min_length, max_length):
        ''' Alias.random_factory expects two arguments: min_length
        and max_length, referring to minimum and maximum lengths
        for aliases generated by function it returns.

        If any of these values is smaller than zero, or if the
        minimum value is larger than the maximum one,
        AliasLengthValueError is expected to be raised
        '''
        self.assertRaises(
            AliasLengthValueError,
            Alias.random_factory,
            min_length,
            max_length
        )

    @parameterized.expand([
        ('larger_than_max_int_32', 2**32, 2**31-10),
        ('for_max_length_larger_than_int_32', 2**31-10, 2**32)
    ])
    def test_random_factory_for_min_int(
            self,
            _,
            min_int,
            min_int_for_max_length
    ):
        ''' Alias.random_factory receives lower and upper limits
        for length of string representation of new aliases as
        its arguments. For these values to be usable, there must be
        integer values that:
        * correspond to string values in these limits
        * are smaller than maximum 32 bit signed integer

        If no such integer exists even for the shortest aliases,
        the whole range of length of alias strings is not available
        for new instances of Alias.
        If no such integers exist for the longest alias strings,
        only part of the range is available.

        In both cases, AliasLengthValueError is expected to be raised
        '''
        min_length = 1
        max_length = 4

        def get_min_value(digit_number):
            min_values = {
                min_length: min_int,
                max_length: min_int_for_max_length
            }
            return min_values.get(digit_number)

        self.numeral_system.get_min_value.side_effect = get_min_value
        self.assertRaises(
            AliasLengthValueError,
            Alias.random_factory,
            min_length,
            max_length
        )

    @parameterized.expand([
        ('smaller_than_max_int_32', 2**31-4),
        ('larger_than_max_int_32', 2**32)
    ])
    @patch('url_shortener.models.randint')
    def test_random_factory_for_max_int(self, _, max_int, randint_mock):
        '''Alias.random_factory calculates lower and upper limits for
        integer representation of instances of Alias to be created by
        the function the method returns.

        The maximum integer can't be larger than maximum value of
        32-bit signed integer. If the max value of integer based only
        on maximum length of string representation of Alias is smaller
        than maximum int32, it is used by the factory function.
        If it's not, maximum int32 is used instead
        '''
        expected_min_int = 3
        self.numeral_system.get_min_value.return_value = expected_min_int
        max_int_32 = 2**31-1
        expected_max_int = min(max_int_32, max_int)
        self.numeral_system.get_max_value.return_value = max_int

        factory = Alias.random_factory(1, 4)
        factory()

        randint_mock.assert_called_once_with(
            expected_min_int,
            expected_max_int
        )

    @parameterized.expand([
        ('non-equal', 1, 3),
        ('equal', 2, 2)
    ])
    def test_random_factory_for_args(self, _, min_length, max_length):
        '''The Alias.random_factory class method is expected to return
        a callable object for correct arguments
        '''
        self.numeral_system.get_min_value.return_value = 0
        self.numeral_system.get_max_value.return_value = 10
        result = Alias.random_factory(min_length, max_length)
        self.assertTrue(callable(result))


class IntegerAliasTest(unittest.TestCase):
    ''' Tests for IntegerAlias class

    :var tested_instance: an instance of the class to be tested
    :var value: a mock used as value parameter to be passed
    to tested methods
    :var dialect: a mock used as dialect parameter to be passed
    to tested methods
    '''
    def setUp(self):
        self.tested_instance = IntegerAlias()
        self.value = Mock()
        self.dialect = Mock()

    @parameterized.expand([
        ['process_bind_param'],
        ['process_literal_param']
    ])
    def test_(self, method_name):
        ''' The method should return an integer value of the
        Alias object passed to them as value param
        '''
        function = getattr(self.tested_instance, method_name)
        expected = self.value.integer
        actual = function(self.value, self.dialect)
        self.assertEqual(expected, actual)

    @patch('url_shortener.models.Alias')
    def test_process_result_value(self, patched_alias_class):
        ''' The process_result_value method should return an
        instance of Alias
        '''
        expected = patched_alias_class(integer=self.value)
        actual = self.tested_instance.process_result_value(
            self.value,
            self.dialect
        )
        self.assertEqual(expected, actual)


class ShortenedUrlTest(unittest.TestCase):
    def setUp(self):
        self.query_patcher = patch('url_shortener.models.ShortenedUrl.query')
        self.query_mock = self.query_patcher.start()

        self.alias_patcher = patch('url_shortener.models.Alias')
        self.alias_mock = self.alias_patcher.start()

    def tearDown(self):
        self.query_patcher.stop()
        self.alias_patcher.stop()

    def test_get_or_create_filters_by_target(self):
        target = 'http://xyz.com'
        ShortenedUrl.get_or_create(target)
        self.query_mock.filter_by.assert_called_once_with(target=target)

    def test_get_or_create_gets_existing_url(self):
        expected = self.query_mock.filter_by.return_value.one_or_none()
        actual = ShortenedUrl.get_or_create('http://xyz.com')
        self.assertEqual(expected, actual)

    def test_get_or_create_creates_new_url(self):
        target = 'http://xyz.com'
        filtered = self.query_mock.filter_by.return_value
        filtered.one_or_none.return_value = None
        expected = target
        actual = ShortenedUrl.get_or_create('http://xyz.com').target
        self.assertEqual(expected, actual)

    def test_get_or_create_finds_multiple_urls(self):
        filtered = self.query_mock.filter_by.return_value
        filtered.one_or_none.side_effect = MultipleResultsFound
        self.assertRaises(
            MultipleResultsFound,
            ShortenedUrl.get_or_create,
            'http://xyz.com'
        )


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
