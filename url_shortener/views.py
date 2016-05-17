# -*- coding: utf-8 -*-
from flask import session, redirect, url_for, flash, render_template

from . import app
from .forms import ShortenedUrlForm
from .models import ShortenedUrl, register


@app.route('/', methods=['GET', 'POST'])
def shorten_url():
    '''Display form and handle request for url shortening

    If short url is successfully created or found for the
    given url, its alias property is saved in session, and
    the function redirects to its route. After redirection,
    the alias is used to query for newly created shortened
    url, and information about it is presented.

    If there are any errors for data entered by the user into
    the input tex field, they are displayed.

    :returns: a response generated by rendering the template,
    either directly or after redirection.
    '''
    form = ShortenedUrlForm()
    if form.validate_on_submit():
        shortened_url = ShortenedUrl.get_or_create(form.url.data)
        register(shortened_url)
        session['new_alias'] = str(shortened_url.alias)
        return redirect(url_for(shorten_url.__name__))
    else:
        for error in form.url.errors:
            flash(error, 'error')
    try:
        new_shortened_url = ShortenedUrl.get_or_404(session['new_alias'])
    except KeyError:
        new_shortened_url = None
    return render_template(
        'shorten_url.html',
        form=form,
        new_shortened_url=new_shortened_url
    )


@app.route('/<alias>')
def redirect_for(alias):
    ''' Redirect to address assigned to given alias

    :param alias: a string value by which we search for
    an associated url. If it is not found, a 404 error
    occurs
    :returns: a redirect to target url of short url, if
    found.
    '''
    shortened_url = ShortenedUrl.get_or_404(alias)
    return redirect(shortened_url.target)


@app.route('/preview/<alias>')
def preview(alias):
    ''' Show the preview for given alias

    The preview contains a short url and a target url
    associated with it.

    :param alias: a string value by which we search
    for an associated url. If it is not found, a 404
    error occurs.
    :returns: a response generated from the preview template
    '''
    shortened_url = ShortenedUrl.get_or_404(alias)
    return render_template(
        'preview.html',
        short_url=shortened_url.short_url,
        target=shortened_url.target
    )


@app.errorhandler(404)
def not_found(error):
    return render_template('not_found.html')


@app.errorhandler(500)
def server_error(error):
    return render_template('server_error.html')
