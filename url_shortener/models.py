# -*- coding: utf-8 -*-
""" This module contains TargetURL class and related classes """
from bisect import bisect_left
from math import log, floor
from random import randint

from cached_property import cached_property
from flask import url_for, current_app
from sqlalchemy import types
from sqlalchemy.exc import IntegrityError

from . import db


class AliasValueError(ValueError):
    """The value of alias is incorrect """


class AliasLengthValueError(ValueError):
    """The value of alias-length related parameter is incorrect """


class AliasType(type):
    def __new__(cls, *args, **kwargs):
        alias_class = type.__new__(cls, *args, **kwargs)
        alias_class.init_random_factory(1, 2)
        return alias_class


class Alias(metaclass=AliasType):
    """ An identifier for shortened URL

    In has two values used as its representations: a string value
    and an integer value, used in short URLs and in database,
    respectively.

    :cvar _chars: a string consisting of characters to be used
    in a string value of an alias.
    :cvar _base: a base of numeral system used to interpret string
    values as integers.
    :cvar _max_int_32: a maximum value of a 32 bit signed integer.

    This value is assumed as maximum allowed for the integers used
    in generation because we assume SQLAlchemy.types.Integer -
    a base type for alias property of TargetURL class - will
    translate into 32 bit signed integer type of underlying
    database engine used by the application.

    :cvar _max_allowed_length: maximum number of characters for
    newly generated alias strings for which there are at least
    some strings whose corresponding integer values are smaller
    or equal to _max_int_32.
    """

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
        only of characters specified in self._chars string.
        If it is None, a value of corresponding property of the object
        will be based on the integer parameter
        :raises AliasValueError: if the alias contains characters that
        are not part of self._chars string, or if both string and
        integer params are None
        """
        self.integer = integer
        if integer is None:
            if string is None:
                raise AliasValueError(
                    'The string and integer arguments cannot both be None'
                )

            self.integer = 0
            for exponent, char in enumerate(reversed(string)):
                digit_value = bisect_left(self._chars, char)
                if (digit_value == self._base or
                        self._chars[digit_value] != char):
                    raise AliasValueError(
                        "The string '{}' contains an unexpected"
                        " character: '{}' ".format(string, char)
                    )
                self.integer += digit_value*self._base**exponent
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

    @classmethod
    def _get_max_int(cls, length):
        """ Get maximum integer value for alias string of given length

        :param length: a number of digits used to write the value
        to be returned in a base cls._base system
        :returns: the largest integer value possible to be written
        as a numeral of given length in the system
        """
        return cls._get_min_int(length + 1) - 1

    @classmethod
    def init_random_factory(cls, min_length, max_length):
        """ Configure factory of randomly generated instances
        of the class

        The arguments provide a range of lengths for string
        representations of instances of Alias to be returned by
        a random alias factory provided by the class. For these values,
        the method calculates a range of integer values corresponding
        to them.

        From that range, only integers smaller than cls._max_int_32
        can be used to generate new aliases.

        :param min_length: a minimum number of characters for string
        representation of the instances returned by the factory
        :param max_length: a maximum number of characters for string
        representation of the instances returned by the factory
        :raises AliasLengthValueError: if:

        * values of any of the parameters are less than zero, or
        * min_length > max_length, or
        * the whole range of alias string lengths, or just part
        of it, is not available for generation due to integer values
        corresponding to it being larger than cls._max_int_32
        """
        if not 0 < min_length <= max_length:
            raise AliasLengthValueError('The length limits are incorrect')
        if cls._max_int_32 < cls._get_min_int(max_length):
            raise AliasLengthValueError(
                'The maximum length of a new alias is too large. The maximum'
                ' acceptable length is: {}'.format(cls._max_allowed_length)
            )

        cls._min_new_int = cls._get_min_int(min_length)
        cls._max_new_int = min(
            cls._max_int_32,
            cls._get_max_int(max_length)
        )

    @classmethod
    def create_random(cls):
        """ Get a randomly generated instance of the class

        The method uses pre-configured class properties
        cls._min_new_int and cls._max_new_int as paramteres for
        pseudo-random integer generation.
        """
        random_integer = randint(cls._min_new_int, cls._max_new_int)
        return cls(integer=random_integer)

    def __str__(self):
        """ Get string representation of the alias

        :returns: a string representing value of the alias as a numeral
        in the base cls._base system.
        """
        if self._string is None:
            value = ''
            integer = self.integer
            while True:
                integer, remainder = divmod(integer, self._base)
                value = self._chars[remainder] + value
                if integer == 0:
                    break
            self._string = value
        return self._string


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


class TargetURL(db.Model):
    """ Represent a URL for which a short alias has been provided
    or requested

    :cvar _alias: a value representing a registered URL in short URLs and
    in database
    """
    _alias = db.Column(
        'alias',
        IntegerAlias,
        primary_key=True,
        default=Alias.create_random
    )
    _value = db.Column('value', db.String(2083), unique=True, nullable=False)

    def __init__(self, target):
        """ Constructor

        :param target: URL represented by the instance
        """
        self._value = target

    def __str__(self):
        return self._value

    def _alternative_url(self, endpoint):
        return url_for(endpoint, _external=True, alias=self._alias)

    @cached_property
    def short_url(self):
        return self._alternative_url('redirect_for')

    @cached_property
    def preview_url(self):
        return self._alternative_url('preview')

    @classmethod
    def get(cls, alias):
        """ Find an existing target URL, or return None

        :param alias: a string representation of alias
        :raises AliasValueError: if the string representation
        of alias is not valid
        :return: an instance of TargetURL representing
        an existing target URL, or None if no target URL
        has been found
        """
        return cls.query.get(Alias(string=alias))

    @classmethod
    def get_or_create(cls, value):
        """ Find an existing target URL or create a new one

        Existing target URLs can be found in database or in
        cache attached to database session.

        :param value: the value of target URL
        :return: an instance of TargetURL, existing or one
        to be registered
        """
        cache = getattr(db.session, '_unique_cache', None)
        if cache is None:
            db.session._unique_cache = cache = {}

        if value in cache:
            return cache[value]

        else:
            with db.session.no_autoflush:
                query = db.session.query(cls)
                target_url = query.filter_by(_value=value).one_or_none()
                if not target_url:
                    target_url = cls(value)
                    db.session.add(target_url)
            cache[value] = target_url
            return target_url

    @classmethod
    def get_or_404(cls, alias):
        """ Find an existing target URL, or abort
        with 404 error code

        :param alias: a string representation of alias
        :raises AliasValueError: if the string representation
        of alias is not valid
        :return: an instance of TargetURL representing an
        existing target URL
        """
        return cls.query.get_or_404(Alias(string=alias))


def commit_changes():
    """ Commits all changes stored in current database session

    The reason for implementing this method instead of simply calling
    commit() on current database session is that the operation includes
    shortening pending target URLs, which may cause some errors that
    require handling.

    The shortening is performed by persisting pending URLs, that is:
    URLs represented by instances of TargetURL that have been added to
    the database session. When it is sucessful, URLs are stored in
    the database, each with a randomly generated alias assigned to it,
    so the application can provide a short URL for each of them.

    Because instances of TargetURL stored in database and managed by
    current database session are guaranteed to be unique on their
    "value" property, the only reason for IntegrityError to be raised
    is an accidental generation of alias value that is already used
    for another URL.

    Aliases are chosen randomly from a set of values with length
    falling between configurable minimum and maximum values. If
    a significant number of aliases from this set is already in use,
    integrity errors become more and more frequent.

    When a number of integrity errors occuring while handling a request
    exceeds a configurable limit, the function logs a warning. By
    paying attention to such occurences becoming more and more
    frequent, administrators can know when it is necessary to increase
    the range of available aliases by increasing their maximum or
    decreasing their minimum length.
    """
    integrity_error_count = 0
    while True:
        try:
            db.session.commit()
            break
        except IntegrityError:
            integrity_error_count += 1
            db.session.rollback()

    limit = current_app.config['INTEGRITY_ERROR_LIMIT']
    if integrity_error_count > limit:
        current_app.logger.warning(
            'Number of integrity errors exceeds the limit: {} > {}'
            ''.format(integrity_error_count, limit)
        )


def configure_random_factory(app_object):
    min_length = app_object.config['MIN_NEW_ALIAS_LENGTH']
    max_length = app_object.config['MAX_NEW_ALIAS_LENGTH']
    Alias.init_random_factory(min_length, max_length)

    msg_tpl = 'Length of newly generated aliases: from {} to {} characters.'
    app_object.logger.info(msg_tpl.format(min_length, max_length))
