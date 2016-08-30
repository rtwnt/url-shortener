# -*- coding: utf-8 -*-
from flask_wtf import Form
from flask_wtf.recaptcha import RecaptchaField, Recaptcha
from wtforms import StringField, validators

from .validation import not_blacklisted_nor_spam


class ShortenedURLForm(Form):
    url = StringField(
        validators=[
            validators.DataRequired(),
            validators.URL(message="A valid URL is required"),
            not_blacklisted_nor_spam
        ]
    )
    recaptcha = RecaptchaField(
        validators=[
            Recaptcha(
                "Please click on the reCAPTCHA field to prove you are a human"
            )
        ]
    )
