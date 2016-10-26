# -*- coding: utf-8 -*-
"""This module contains code belonging to domain and
persistence layers
"""
from bisect import bisect_left
from math import log, floor
from random import randint, choice
from string import ascii_lowercase, digits

from cached_property import cached_property

from flask import url_for, Flask
from flask_sqlalchemy import SQLAlchemy
from injector import (
    inject, singleton, Module, Key, InstanceProvider
)
from sqlalchemy import types
from sqlalchemy.exc import IntegrityError


class AlphabetValueError(ValueError):
    """The value of alias alphabet is incorrect"""


class CharacterValueError(ValueError):
    """The alphabet doesn't contain the character"""


class AliasValueError(ValueError):
    """The value of alias is incorrect """


class AliasLengthValueError(ValueError):
    """The value of alias-length related parameter is incorrect """


class AliasAlphabet(object):
    """ Represents an alphabet of characters used for creating
    alias strings and provides methods for creating alias strings

    :cvar INTAB: a string containing characters to be replaced
    with their homoglyphs, if they are present in a string
    :cvar OUTTAB: a string containing characters to replace their
    corresponding characters in INTAB
    :cvar TRANSLATION: a translation table for replacing characters
    with their homoglyphs
    """
    INTAB = 'lIoBzZsSb9'
    OUTTAB = '110822556g'
    TRANSLATION = str.maketrans(INTAB, OUTTAB)

    def __init__(self, characters, min_length, max_length):
        """Initialize a new instance

        :param characters: a string containing characters to be
        inlcuded in the alphabet

        To avoid generating aliases with characters that can be
        confused with each other, characters specified in the INTAB
        class property can't be specified as part of the alphabet.

        :param min_length: a minimum length of a newly generated
        alias string
        :param max_length: a maximum length of a newly generated
        alias string
        :raises AlphabetValueError: if characters parameter contains
        any character specified in the INTAB
        :raises AliasLengthValueError: if min_length and max_length
        don't fulfill the condition: 0 < min_length <= max_length
        """

        self._set_characters(characters)
        self._set_length_range(min_length, max_length)

    @classmethod
    def from_chars_with_homoglyphs(cls, characters, *args, **kwargs):
        """Create a new instance using characters that may contain
        unsupported, potentially confusing characters

        The potentially confusing characters are simply removed.

        :param characters: a string containing characters to be
        inlcuded in the alphabet

        Only those characters that aren't specified in INTAB are
        to be included in the new instance.

        :param min_length: a minimum length of a newly generated
        alias string
        :param max_length: a maximum length of a newly generated
        alias string
        """
        for char in cls.INTAB:
            characters = characters.replace(char, '')
        return cls(characters, *args, **kwargs)

    def _set_characters(self, characters):
        """Assign the characters to the instance and adjust
        replacements for multiletter homoglyphs

        :param characters: a string containing characters to be
        inlcuded in the alphabet.

        To avoid generating aliases with characters that can be
        confused with each other, characters specified in the INTAB
        class property can't be specified as part of the alphabet.

        :raises AlphabetValueError: if characters parameter contains
        any character specified in the INTAB
        """
        unsupported_chars = [c for c in self.INTAB if c in characters]
        if unsupported_chars:
            raise AlphabetValueError(
                "The alias alphabet '{}' contains unsupported characters:"
                " {}".format(characters, ', '.join(unsupported_chars))
            )

        self._characters = ''.join(sorted(characters))

        homoglyphs = {'rn': 'm', 'vv': 'w', 'cj': 'g', 'ci': 'a', 'c1': 'd'}
        self._homoglyphs = {
            g: r for g, r in homoglyphs.items() if r in characters
        }

    def _set_length_range(self, min_length, max_length):
        """Set a min and max length of newly generated random aliases

        :param min_length: a minimum length of a newly generated
        alias string
        :param max_length: a maximum length of a newly generated
        alias string
        :raises AliasLengthValueError: if min_length and max_length
        don't fulfill the condition: 0 < min_length <= max_length
        """
        if not 0 < min_length <= max_length:
            raise AliasLengthValueError(
                'The length limits are incorrect = the condition'
                ' 0 < min_length <= max_length is not fulfilled for'
                ' min_length = {} and max_length = {}'.format(
                    min_length,
                    max_length
                )
            )
        self._min_length = min_length
        self._max_length = max_length

    def create_random(self):
        """ Create a random alias for a preconfigured length range

        The alias is generated as a string of randomly chosen length
        value between self._min_length and self._max_length, consisting
        of randomly chosen alphabet characters.

        After being generated, the string is sanitized by replacing
        multiletter homoglyphs that could be present in it. That may
        shorten the alias, so its length is tested and, if it happens
        to be shorter than the minimum, the generation is repeated.

        :return: a randomly generated alias string
        """
        while True:
            length = randint(self._min_length, self._max_length)
            alias = ''.join(choice(self._characters) for i in range(length))
            alias = self._replace_multiletter_homoglyphs(alias)
            if len(alias) >= self._min_length:
                return alias

    def _replace_multiletter_homoglyphs(self, string):
        """Get a string with multiletter homoglyphs replaced
        by their single-character equivalents

        :param string: a string alias
        :return: a string alias with multiletter homoglyphs replaced
        by their single-character equivalents
        """
        for orig, repl in self._homoglyphs.items():
            string = string.replace(orig, repl)
        return string

    def from_string(self, string):
        """Get a valid alias string without potentially confusing
        characters

        :param string: an original alias string
        :return: a string resulting from replacement of potentially
        confusing characters with their homoglyphs included in
        the alphabet
        :raises AliasValueError: if the string generated from
        the original string still contains unsupported characters.
        """
        string = string.translate(self.TRANSLATION)
        string = self._replace_multiletter_homoglyphs(string)

        unexpected_chars = [x for x in string if x not in self._characters]
        if unexpected_chars:
            raise AliasValueError(
                "The string '{}' contains unsupported characters: "
                "".format(string, ', '.join(unexpected_chars))
            )
        return string

    def __len__(self):
        """Get the length of the alphabet

        :returns: the length as a number of characters in the alphabet
        """
        return len(self._characters)

    def index(self, character):
        """Get index of a character in the alphabet

        :param character: a character whose index in the alphabet is
        to be returned
        :returns: index of the character
        :raises CharacterValueError: if the character is not part of
        the alphabet
        """
        index = bisect_left(self._characters, character)
        if index == len(self) or self._characters[index] != character:
            raise CharacterValueError(
                "AliasAlphabet.index(character): '{}' not in alphabet".format(
                    character
                )
            )

        return index

    def __getitem__(self, index):
        """Get a character corresponding to given index

        :param index: a postion of a character to be returned
        :returns: a character in the alphabet at the given index
        :raises IndexError: if the index is out of range
        """
        return self._characters[index]

    def __str__(self):
        return self._characters


class IntegerAlias(types.TypeDecorator):
    """A custom database column type converting between integers
    and alias strings

    :cvar impl: implementation type of the class
    :cvar _max_int_32: a maximum value of a 32 bit signed integer

    This value is assumed as maximum allowed for the integers used
    in generation because we assume the implementation type will
    translate into 32 bit signed integer type of underlying database
    engine used by the application.
    """

    impl = types.Integer
    _max_int_32 = 2**31 - 1

    @inject
    def __init__(self, alphabet):
        """ Initialize a new instance

        :param alphabet: an instance of AliasAlphabet to be used
        for convertion
        """

        base = len(alphabet)
        max_safe_length = int(floor(log(self._max_int_32, base)))
        max_length = alphabet._max_length

        if max_length > max_safe_length:
            raise AlphabetValueError(
                'The alias alphabet can be used to generate strings of'
                ' a length up to {} characters, but such aliases can not be'
                ' converted to an integer smaller than max int32'.format(
                    max_length
                )
            )

        self._base = base
        self._alphabet = alphabet

        super(IntegerAlias, self).__init__()

    def process_bind_param(self, value, dialect):
        """Get integer representation of given string alias

        :param value: an alias string
        :param dialect: an object implementing
        sqlalchemy.engine.interfaces.Dialect, representing a dialect
        used by the database
        :returns: an integer corresponding to the alias string
        :raises AliasValueError: if value is not a valid alias string,
        for example: if it contains characters that are not part
        of the alphabet
        """
        integer = 0
        valid_alias = self._alphabet.from_string(value)

        for exponent, char in enumerate(reversed(valid_alias)):
            digit_value = self._alphabet.index(char)
            integer += digit_value * self._base**exponent

        return integer

    process_literal_param = process_bind_param

    def process_result_value(self, value, dialect):
        """Get alias string for given integer

        :param value: an integer representing alias string
        :param dialect: an object implementing
        sqlalchemy.engine.interfaces.Dialect, representing a dialect
        used by the database
        :returns: a string converted from the integer
        """
        string = ''
        while True:
            value, remainder = divmod(value, self._base)
            string = self._alphabet[remainder] + string
            if value == 0:
                break

        return string


class BaseTargetURL(object):
    """A base class for classes representing target URLs"""

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
        return self._alternative_url('url_shortener.redirect_for')

    @cached_property
    def preview_url(self):
        return self._alternative_url('url_shortener.preview')

    @classmethod
    def get_or_create(cls, value):
        """ Find an existing target URL or create a new one

        Existing target URLs can be found in database or in
        cache attached to database session.

        :param value: the value of target URL
        :return: an instance of the class, existing or one
        to be registered
        """
        cache = getattr(cls._session, '_unique_cache', None)
        if cache is None:
            cls._session._unique_cache = cache = {}

        if value in cache:
            return cache[value]

        else:
            with cls._session.no_autoflush:
                query = cls._session.query(cls)
                target_url = query.filter_by(_value=value).one_or_none()
                if not target_url:
                    target_url = cls(value)
                    cls._session.add(target_url)
            cache[value] = target_url
            return target_url


commit_changes = Key('commit_changes')


@inject
def get_commit_changes(app: Flask, db: SQLAlchemy):
    """Get commit_changes function that uses the objects passed here

    :param app: an instance of Flask representing the current
    application
    :param db: an instance of SQLAlchemy for the database being used
    :returns: a function to be used for commiting changes
    """
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

        limit = app.config['INTEGRITY_ERROR_LIMIT']
        if integrity_error_count > limit:
            app.logger.warning(
                'Number of integrity errors exceeds the limit: {} > {}'
                ''.format(integrity_error_count, limit)
            )
    return commit_changes


target_url_class = Key('target_url_class')


class DomainAndPersistenceModule(Module):

    def __init__(self, app):
        self.app = app
        # See http://flask-sqlalchemy.pocoo.org/2.1/config/
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.db = SQLAlchemy(app)
        self.db.create_all()

    def configure(self, binder):
        binder.bind(SQLAlchemy, to=self.db, scope=singleton)
        binder.bind(
            target_url_class,
            to=InstanceProvider(
                self.get_target_url_class()
            ),
            scope=singleton
        )
        binder.bind(commit_changes, to=get_commit_changes, scope=singleton)

    def get_target_url_class(self):
        """Get a configured subclass of BaseTargetURL and db.Model

        :returns: a subclass of BaseTargetURL and db.Model to be used by
        the application.
        """

        integer_alias = IntegerAlias(self.get_alias_alphabet())

        class TargetURL(BaseTargetURL, self.db.Model):
            """A class of URLs for which a short alias has been
            provided or requested

            :cvar _session: a database session to be used by the class
            :ivar _alias: a value representing a registered URL in
            short URLs and in database.
            :ivar _value: a value of a target URL
            """
            _session = self.db.session

            _alias = self.db.Column(
                'alias',
                integer_alias,
                primary_key=True,
                default=integer_alias._alphabet.create_random
            )

            _value = self.db.Column(
                'value',
                self.db.String(2083),
                unique=True,
                nullable=False
            )

        return TargetURL

    def get_alias_alphabet(self):
        alphabet = AliasAlphabet.from_chars_with_homoglyphs(
            digits + ascii_lowercase,
            self.app.config['MIN_NEW_ALIAS_LENGTH'],
            self.app.config['MAX_NEW_ALIAS_LENGTH']
        )

        self.app.logger.info(
            "Providing an instance of AliasAlphabet. It contains"
            " the following characters:\n{0}.\n\nIt can be used to generate"
            " aliases from {0._min_length} to {0._max_length}"
            " characters long.".format(
                alphabet
            )
        )

        return alphabet
