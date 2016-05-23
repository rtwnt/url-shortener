# -*- coding: utf-8 -*-
from flask_wtf import Form
from wtforms import StringField, validators

from .validation import not_spam


class ShortenedUrlForm(Form):
    url = StringField(
        'Url to be shortened',
        [
            validators.DataRequired(),
            validators.URL(message="A valid url is required"),
            not_spam
        ]
    )
