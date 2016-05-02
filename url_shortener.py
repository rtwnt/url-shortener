# -*- coding: utf-8 -*-

from bisect import bisect_left


class Slug(object):
    ''' An identifier for shortened url

    In has two values used as its representations: a string value
    and an integer value, used in short urls and in database,
    respectively.

    :var CHARS: string containing characters allowed to be used
    in a slug. The characters are used as digits of a numerical system
    used to convert between the string and integer representations.
    :var BASE: a base of numeral system used to convert between
    the string and integer representations.
    '''

    CHARS = '0123456789abcdefghijkmnopqrstuvwxyz'
    BASE = len(CHARS)

    def __init__(self, integer=None, string=None):
        ''' Initialize new instance

        :param integer: a value representing the slug as an integer.
        It can not be None while string is None. If it is None, a
        corresponding property of the object will be based on
        the string parameter
        :param string: a value representing the slug as a string.
        It can not be None while integer is None, and it has to consist
        only of characters specified by the CHARS class property.
        If it is None, a value of corresponding property of the object
        will be based on the integer parameter
        :raises ValueError: if the slug contains characters that are not
        in self.CHARS property, or if both string and integer params
        are None
        '''
        if string is not None:
            forbidden = [d for d in string if d not in self.CHARS]
            if forbidden:
                msg_tpl = "The slug '{}' contains forbidden characters: '{}'"
                raise ValueError(msg_tpl.format(string, forbidden))
        elif integer is None:
            raise ValueError(
                'The string and integer arguments cannot both be None'
            )

        self._string = string

        self.integer = integer
        if integer is None:
            value = 0
            for exponent, char in enumerate(reversed(string)):
                digit_value = bisect_left(self.CHARS, char)
                value += digit_value*self.BASE**exponent
            self.integer = value

    def __str__(self):
        ''' Get string representation of the slug

        :returns: a string representing value of the slug as a numeral
        of base specified for the class. If the object has been
        initialized with integer as its only representation,
        the numeral will be derived from it using the base.
        '''
        if self._string is None:
            value = ''
            integer = self.integer
            while True:
                integer, remainder = divmod(integer, self.BASE)
                value = self.CHARS[remainder] + value
                if integer == 0:
                    break
            self._string = value
        return self._string


if __name__ == '__main__':
    pass
