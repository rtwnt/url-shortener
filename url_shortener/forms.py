# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from flask_wtf.recaptcha import RecaptchaField, Recaptcha
from injector import Module, provider, Key, singleton
from wtforms import StringField, validators

from .validation import url_validator, BlacklistValidator


class ShortenedURLForm(FlaskForm):
    url = StringField(
        validators=[
            validators.DataRequired(message='A target URL is required.'),
            validators.URL(message='A valid URL is required.'),
            url_validator.assert_not_blacklisted
        ],
        render_kw={'placeholder': 'Original URL'}
    )
    recaptcha = RecaptchaField(
        validators=[
            Recaptcha(
                'Please click on the reCAPTCHA field '
                'to prove you are a human.'
            )
        ]
    )


url_form_class = Key('url_form_class')


class FormModule(Module):
    @singleton
    @provider
    def get_url_form_class(
        self,
        url_validator: BlacklistValidator
    ) -> url_form_class:

        url_validators = [
            validators.DataRequired(message='A target URL is required.'),
            validators.URL(message='A valid URL is required.'),
            url_validator.assert_not_blacklisted
        ]
        msg = 'Please click on the reCAPTCHA field to prove you are a human.'
        recaptcha_validators = [Recaptcha(msg)]

        class URLForm(FlaskForm):
            url = StringField(
                validators=url_validators,
                render_kw={'placeholder': 'Original URL'}
            )
            recaptcha = RecaptchaField(validators=recaptcha_validators)

        return URLForm
