# -*- coding: utf-8 -*-

""" This module contains functions used as
SQLAlchemy event handlers
"""
from sqlalchemy import event

from .models import Alias, ShortenedURL


@event.listens_for(ShortenedURL, 'before_insert')
def assign_alias_before_insert(mapper, connection, target):
    target.alias = Alias.create_random()
