# -*- coding: utf-8 -*-

import unittest

from nose_parameterized import parameterized

from url_shortener import Slug, SlugValueError


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
        Slug.CHARS = 'abc'
        Slug.BASE = 3

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


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
