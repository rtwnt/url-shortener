# -*- coding: utf-8 -*-

"""Form classes and form class factories used by the application."""
from flask_wtf import FlaskForm
from flask_wtf.recaptcha import RecaptchaField, Recaptcha
from injector import inject, Key, singleton
from wtforms import StringField, validators

from .validation import BlacklistValidator


url_form_class = Key('url_form_class')


@inject
def get_url_form_class(url_validator: BlacklistValidator):
    """Get a dynamically created form class.

    :param url_validator: a blacklist validator for URL values
    :return: a subclass of FlaskForm to be used by an instance of
    application object
    """
    url_validators = [
        validators.DataRequired(message='A target URL is required.'),
        validators.URL(message='A valid URL is required.'),
        url_validator.assert_not_blacklisted
    ]

    msg = 'Please click on the reCAPTCHA field to prove you are a human.'
    recaptcha_validators = [Recaptcha(msg)]

    class URLForm(FlaskForm):
        """A form class for submitting a valid and nom-malicious URL."""

        url = StringField(
            validators=url_validators,
            render_kw={'placeholder': 'Original URL'}
        )
        recaptcha = RecaptchaField(validators=recaptcha_validators)

    return URLForm


def configure(binder):
    """Configure dependencies.

    :param binder: an instance of injector.Binder used for binding
    interfaces to implementations
    """
    binder.bind(url_form_class, to=get_url_form_class, scope=singleton)
