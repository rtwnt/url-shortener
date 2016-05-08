# -*- coding: utf-8 -*-

''' This module contains functions used as
SQLAlchemy event handlers
'''
from sqlalchemy import event

from .models import Alias, ShortenedUrl


random_alias_generator = Alias.random_factory(1, 4)


@event.listens_for(ShortenedUrl, 'before_insert')
def assign_alias_before_insert(mapper, connection, target):
    target.alias = random_alias_generator()
