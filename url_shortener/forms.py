# -*- coding: utf-8 -*-
from flask_wtf import Form
from wtforms import StringField


class ShortenedUrlForm(Form):
    url = StringField('Url to be shortened')
