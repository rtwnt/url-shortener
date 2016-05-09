# -*- coding: utf-8 -*-

''' This module contains functions used as
SQLAlchemy event handlers
'''
from sqlalchemy import event

from .models import Alias, ShortenedUrl
from . import app


random_alias_generator = Alias.random_factory(
    app.config['MIN_NEW_ALIAS_LENGTH'],
    app.config['MAX_NEW_ALIAS_LENGTH']
)


@event.listens_for(ShortenedUrl, 'before_insert')
def assign_alias_before_insert(mapper, connection, target):
    target.alias = random_alias_generator()
