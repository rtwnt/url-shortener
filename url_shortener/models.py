# -*- coding: utf-8 -*-
''' This module contains ShortenedUrl class and related classes '''
from bisect import bisect_left
from random import randint

from cached_property import cached_property
from flask import url_for
from sqlalchemy import types

from . import db


class AliasValueError(ValueError):
    '''The value of alias is incorrect '''


class AliasLengthValueError(ValueError):
    '''The value of alias-length related parameter is incorrect '''


class NumeralValueError(ValueError):
    '''The value of a numeral is incorrect'''


class NumeralSystem(object):
    ''' Represents a numeral system. Provides conversion methods
    and other related operations

    :param characters: characters to be used for numerals written
    in the system
    '''
    def __init__(self, characters):
        self._chars = characters
        self._base = len(characters)

    def to_string(self, integer):
        ''' Convert the value to a numeral in the system

        :param integer: a value to be converted
        :returns: a string representing value of the integer as a numeral
        in the numeral system
        '''
        value = ''
        while True:
            integer, remainder = divmod(integer, self._base)
            value = self._chars[remainder] + value
            if integer == 0:
                break
        return value

    def to_integer(self, string):
        ''' Convert given string to its value in the numeral system

        :param string: a value to be converted
        :raises NumeralValueError: if the string contains any
        characters not used by the numeral system
        :returns: an integer representing the value of the string
        interpreted as a numeral in the system
        '''
        value = 0
        for exponent, char in enumerate(reversed(string)):
            digit_value = bisect_left(self._chars, char)
            if digit_value == self._base or self._chars[digit_value] != char:
                msg_tpl = (
                    "The character '{}' is not used by the numeral system"
                )
                raise NumeralValueError(msg_tpl.format(char))
            value += digit_value*self._base**exponent
        return value

    def get_min_value(self, length):
        ''' Get a minimum value of a numeral of given length

        :param length: a number of digits used to write the number
        in the system
        :returns: the smallest numerical value possible to be written
        as numeral of given length in the system
        '''
        return self._base**(length - 1)

    def get_max_value(self, length):
        ''' Get a maximum value of a numeral of given length

        :param length: a number of digits used to write the number
        :returns: the largest numerical value possible to be written
        as numeral of given length in the system
        '''
        return (self._base - 1)*(1 - self._base**length)/(1 - self._base)


class Alias(object):
    ''' An identifier for shortened url

    In has two values used as its representations: a string value
    and an integer value, used in short urls and in database,
    respectively.

    :var _SYSTEM: an instance of NumeralSystem usted by the class and
    its instances
    '''

    _SYSTEM = NumeralSystem('0123456789abcdefghijkmnopqrstuvwxyz')

    def __init__(self, integer=None, string=None):
        ''' Initialize new instance

        :param integer: a value representing the alias as an integer.
        It can not be None while string is None. If it is None, a
        corresponding property of the object will be based on
        the string parameter
        :param string: a value representing the alias as a string.
        It can not be None while integer is None, and it has to consist
        only of characters used by the numeral system.
        If it is None, a value of corresponding property of the object
        will be based on the integer parameter
        :raises AliasValueError: if the alias contains characters that are not
        used by the numeral system, or if both string and integer
        params are None
        '''
        self.integer = integer
        if integer is None:
            if string is None:
                raise AliasValueError(
                    'The string and integer arguments cannot both be None'
                )
            try:
                self.integer = self._SYSTEM.to_integer(string)
            except NumeralValueError as ex:
                raise AliasValueError(
                    "The string '{}'  is not a valid alias ".format(string)
                ) from ex
        self._string = string

    def __str__(self):
        ''' Get string representation of the alias

        :returns: a string representing value of the alias as a numeral
        in the numeral system. If the object has been
        initialized with integer as its only representation,
        the numeral will be derived from it using the system.
        '''
        if self._string is None:
            self._string = self._SYSTEM.to_string(self.integer)
        return self._string

    @classmethod
    def random_factory(cls, min_length, max_length):
        ''' Get a function returning new instances of the class
        with a random integer as argument

        The arguments provide a range of lengths for string
        representations of instances of Alias to be returned
        by the factory. For these values, the method calculates
        a range of integer values corresponding to them.

        From that range, only integers smaller than maximum
        32-bit integer can be used to generate new aliases.

        :param min_length: a minimum number of characters for string
        representation of the instances returned by the factory
        :param max_length: a maximum number of characters for string
        representation of the instances returned by the factory
        :raises AliasLengthValueError: if:

        * values of any of the parameters are less than zero, or
        * max_length > min_length, or
        * the whole range of alias string lengths, or just part
        of it, is not available for generation due to integer values
        corresponding to it being larger than maximum 32-bit
        signed integer.

        This value is assumed as maximum allowed for the integers used
        in generation because we assume SQLAlchemy.types.Integer -
        a base type for alias property of ShortenedUrl class - will
        translate into 32 bit signed integer type of underlying
        database engine used by the application.
        :returns: a function returning instances of the class
        based on random integers with a pre-calculated range
        '''

        if not 0 < min_length <= max_length:
            raise AliasLengthValueError('The length limits are incorrect')
        max_int_32 = 2**31 - 1
        min_integer = cls._SYSTEM.get_min_value(min_length)
        if min_integer > max_int_32:
            raise AliasLengthValueError(
                'The minimum length of a new alias is too large'
            )

        if (min_length < max_length and
                cls._SYSTEM.get_min_value(max_length) > max_int_32):
            raise AliasLengthValueError(
                'The maximum length of a new alias is too large'
            )

        max_integer = min(max_int_32, cls._SYSTEM.get_max_value(max_length))

        def factory():
            random_integer = randint(min_integer, max_integer)
            return cls(integer=random_integer)
        return factory


class IntegerAlias(types.TypeDecorator):
    ''' Converts between database integers and
    instances of Alias
    '''

    impl = types.Integer

    def process_bind_param(self, value, dialect):
        return value.integer

    process_literal_param = process_bind_param

    def process_result_value(self, value, dialect):
        return Alias(integer=value)


class ShortenedUrl(db.Model):
    ''' Represents a url for which a short alias has been created

    :var alias: a value representing a registered url in short urls and
    in database
    '''
    alias = db.Column(IntegerAlias, primary_key=True)
    target = db.Column(db.String(2083), unique=True)

    def __init__(self, target):
        ''' Constructor

        :param target: url represented by the instance
        '''
        self.target = target

    def __str__(self):
        return self.target

    def _alternative_url(self, endpoint):
        return url_for(endpoint, _external=True, alias=self.alias)

    @cached_property
    def short_url(self):
        return self._alternative_url('redirect_for')

    @cached_property
    def preview_url(self):
        return self._alternative_url('preview')
