# -*- coding: utf-8 -*-

import unittest
from unittest.mock import Mock, patch

from nose_parameterized import parameterized

from url_shortener import Slug, SlugValueError, IntegerSlug


class SlugTest(unittest.TestCase):
    ''' Tests for Slug class

    :var SLUG_INTEGER: maps string values of slugs used in tests to
    corresponding integers.
    :var INTEGERS: a list of lists, each containing one of the integers
    specified in SLUG_INTEGER. Used as an argument for
    parameterized.expand()
    :var SLUGS_TO_INTEGERS: a list containing tuples, each with a pair of
    slug string and its corresponding integer. Used as an argument for
    parameterized.expand()
    '''
    SLUG_INTEGER = {
        'baa': 1*3**2,
        'ccb': 2*3**2+2*3+1,
        'caca': 2*3**3+2*3,
        'ccc': 2*3**2+2*3+2,
        'a': 0
    }
    INTEGERS = [[v] for v in SLUG_INTEGER.values()]
    SLUGS_TO_INTEGERS = SLUG_INTEGER.items()

    @classmethod
    def setUpClass(cls):
        Slug._CHARS = 'abc'
        Slug._BASE = 3

    def test_init_for_invalid_string(self):
        ''' The string contains forbidden characters '''
        string = 'abcd'
        self.assertRaises(SlugValueError, Slug, None, string)

    def test_init_for_invalid_arg_set(self):
        ''' The arguments integer and string can't both be None '''
        self.assertRaises(SlugValueError, Slug, None, None)

    @parameterized.expand(SLUGS_TO_INTEGERS)
    def test_init_for_generated_integer(self, string, expected_integer):
        ''' The integer value of slug should be properly calculated
        when integer == None '''
        instance = Slug(string=string)
        actual_integer = instance.integer
        self.assertEqual(expected_integer, actual_integer)

    @parameterized.expand(INTEGERS)
    def test_init_for_string_being_none(self, integer):
        ''' The string value should not be generated during
        object initialization'''
        instance = Slug(integer=integer)
        self.assertIsNone(instance._string)

    @parameterized.expand(SLUGS_TO_INTEGERS)
    def test_str_for_string_being_none(self, expected_string, integer):
        ''' The __str__ method should properly generate string
        based on objects .integer property '''
        instance = Slug(integer=integer)
        actual_string = str(instance)
        self.assertEqual(expected_string, actual_string)


class IntegerSlugTest(unittest.TestCase):
    ''' Tests for IntegerSlug class

    :var tested_instance: an instance of the class to be tested
    :var value: a mock used as value parameter to be passed
    to tested methods
    :var dialect: a mock used as dialect parameter to be passed
    to tested methods
    '''
    def setUp(self):
        self.tested_instance = IntegerSlug()
        self.value = Mock()
        self.dialect = Mock()

    @parameterized.expand([
        ['process_bind_param'],
        ['process_literal_param']
    ])
    def test_(self, method_name):
        ''' The method should return an integer value of the
        Slug object passed to them as value param
        '''
        function = getattr(self.tested_instance, method_name)
        expected = self.value.integer
        actual = function(self.value, self.dialect)
        self.assertEqual(expected, actual)

    @patch('url_shortener.Slug')
    def test_process_result_value(self, patched_slug_class):
        ''' The process_result_value method should return an
        instance of Slug
        '''
        expected = patched_slug_class(integer=self.value)
        actual = self.tested_instance.process_result_value(
            self.value,
            self.dialect
        )
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
