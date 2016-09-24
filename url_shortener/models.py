# -*- coding: utf-8 -*-
""" This module contains ShortenedURL class and related classes """
from bisect import bisect_left
from math import log, floor
from random import randint

from cached_property import cached_property
from flask import url_for, abort
from sqlalchemy import types
from sqlalchemy.exc import IntegrityError

from . import db, app


class AliasValueError(ValueError):
    """The value of alias is incorrect """


class AliasLengthValueError(ValueError):
    """The value of alias-length related parameter is incorrect """


class NumeralValueError(ValueError):
    """The value of a numeral is incorrect"""


class RegistrationRetryLimitExceeded(Exception):
    """The maximum number of attempts at retrying to register
    a new short URL has been exceeded """


class NumeralSystem(object):
    """ Represents a numeral system. Provides conversion methods
    and other related operations

    :param characters: characters to be used for numerals written
    in the system
    """
    def __init__(self, characters):
        self._chars = characters
        self._base = len(characters)

    def to_string(self, integer):
        """ Convert the value to a numeral in the system

        :param integer: a value to be converted
        :returns: a string representing value of the integer as a numeral
        in the numeral system
        """
        value = ''
        while True:
            integer, remainder = divmod(integer, self._base)
            value = self._chars[remainder] + value
            if integer == 0:
                break
        return value

    def to_integer(self, string):
        """ Convert given string to its value in the numeral system

        :param string: a value to be converted
        :raises NumeralValueError: if the string contains any
        characters not used by the numeral system
        :returns: an integer representing the value of the string
        interpreted as a numeral in the system
        """
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
        """ Get a minimum integer value of a numeral of given length

        :param length: a number of digits used to write the number
        in the system
        :returns: the smallest integer value possible to be written
        as a numeral of given length in the system
        """
        return self._base**(length - 1)

    def get_max_value(self, length):
        """ Get a maximum integer value of a numeral of given length

        :param length: a number of digits used to write the number
        :returns: the largest integer value possible to be written
        as a numeral of given length in the system
        """
        return self.get_min_value(length + 1) - 1


class Alias(object):
    """ An identifier for shortened URL

    In has two values used as its representations: a string value
    and an integer value, used in short URLs and in database,
    respectively.

    :cvar _SYSTEM: an instance of NumeralSystem usted by the class and
    its instances

    :cvar _chars: a string consisting of characters to be used
    in a string value of an alias.
    :cvar _base: a base of numeral system used to interpret string
    values as integers.
    :cvar _max_int_32: a maximum value of a 32 bit signed integer.

    This value is assumed as maximum allowed for the integers used
    in generation because we assume SQLAlchemy.types.Integer -
    a base type for alias property of ShortenedURL class - will
    translate into 32 bit signed integer type of underlying
    database engine used by the application.

    :cvar _max_allowed_length: maximum number of characters for
    newly generated alias strings for which there are at least
    some strings whose corresponding integer values are smaller
    or equal to _max_int_32.
    """

    _SYSTEM = NumeralSystem('0123456789abcdefghijkmnopqrstuvwxyz')
    _chars = '0123456789abcdefghijkmnopqrstuvwxyz'
    _base = len(_chars)
    _max_int_32 = 2**31 - 1
    _max_allowed_length = floor(log(_max_int_32, _base)) + 1

    def __init__(self, integer=None, string=None):
        """ Initialize new instance

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
        """
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

    @classmethod
    def _get_min_int(cls, length):
        """ Get minimum integer value for alias string of given length

        :param length: a number of digits used to write the value
        to be returned in a base cls._base system
        :returns: the smallest integer value possible to be written
        as a numeral of given length in the system
        """
        return cls._base**(length - 1)

    def __str__(self):
        """ Get string representation of the alias

        :returns: a string representing value of the alias as a numeral
        in the numeral system. If the object has been
        initialized with integer as its only representation,
        the numeral will be derived from it using the system.
        """
        if self._string is None:
            self._string = self._SYSTEM.to_string(self.integer)
        return self._string

    @classmethod
    def random_factory(cls, min_length, max_length):
        """ Get a function returning new instances of the class
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
        a base type for alias property of ShortenedURL class - will
        translate into 32 bit signed integer type of underlying
        database engine used by the application.
        :returns: a function returning instances of the class
        based on random integers with a pre-calculated range
        """

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
    """ Converts between database integers and
    instances of Alias
    """

    impl = types.Integer

    def process_bind_param(self, value, dialect):
        return value.integer

    process_literal_param = process_bind_param

    def process_result_value(self, value, dialect):
        return Alias(integer=value)


class ShortenedURL(db.Model):
    """ Represents a URL for which a short alias has been created

    :cvar alias: a value representing a registered URL in short URLs and
    in database
    """
    alias = db.Column(IntegerAlias, primary_key=True)
    target = db.Column(db.String(2083), unique=True)

    def __init__(self, target):
        """ Constructor

        :param target: URL represented by the instance
        """
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

    @classmethod
    def get_or_create(cls, target_url):
        """ Find an existing shortened URL, or
        create a new one

        :param target_url: the target of shortened URL
        :return: an instance of ShortenedURL, existing or one
        to be registered
        """
        shortened_url = cls.query.filter_by(target=target_url).one_or_none()
        if shortened_url is None:
            shortened_url = cls(target_url)
        return shortened_url

    @classmethod
    def get_or_404(cls, alias):
        """ Find an existing shortened URL, or abort
        with 404 error code

        :param alias: a string representation of alias
        :raises AliasValueError: if the string representation
        of alias is not valid
        :return: an instance of ShortenedURL representing an
        existing shortened URL
        """
        try:
            valid_alias = Alias(string=alias)
        except AliasValueError:
            abort(404)
        return cls.query.get_or_404(valid_alias)


def register(shortened_url):
    """ Register a shortened URL object by persisting it

    :param shortened_url: an instance of ShortenedURL to be registered
    :raises RegistrationRetryLimitExceeded: if the application exceeded
    the maximum number of attempts at shortening a URL,
    without success.

    Registered shortened URLs get aliases chosen randomly from a set
    of values with length falling between configurable minimum
    and maximum values. If a significant number of aliases from
    this set is already in use, exceeding the retry limit becomes more
    and more likely.
    """
    retry_limit = app.config['REGISTRATION_RETRY_LIMIT']
    for _ in range(retry_limit):
        try:
            db.session.add(shortened_url)
            db.session.commit()
            return
        except IntegrityError as ex:
            db.session.rollback()
            msg = (
                'An integrity error occured during registration of'
                ' shortened URL: {}'.format(ex)
            )
            app.logger.warning(msg)
    msg_tpl = 'Registration retry limit of {} has been reached'
    raise RegistrationRetryLimitExceeded(msg_tpl.format(retry_limit))
