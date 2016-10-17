# -*- coding: utf-8 -*-
from codecs import open
import re
from setuptools import setup


def read_attributes(string, *names):
    regex_tpl = r'^__{}__\s*=\s*[\'"]([^\'"]*)[\'"]'

    def read(name):
        regex = regex_tpl.format(name)
        return re.search(regex, string, re.MULTILINE).group(1)

    return [read(n) for n in names]

with open('url_shortener/__init__.py', 'r') as fd:
    content = fd.read()
    name, version, author, email, _license = read_attributes(
        content,
        'title',
        'version',
        'author',
        'email',
        'license'
    )

with open('README.rst', 'r', 'utf-8') as f:
    readme = f.read()


install_requires = [
    'Flask',
    'Flask-Injector',
    'Flask-Migrate',
    'Flask-SQLAlchemy',
    'Flask-WTF',
    'cached-property',
    'spam-lists',
]

tests_require = ['nose-parameterized']

setup(
    name=name,
    version=version,
    description='A URL shortener application',
    long_description=readme,
    author=author,
    author_email=email,
    url='https://github.com/piotr-rusin/url-shortener',
    packages=['url_shortener', 'test', 'test.unit'],
    package_data={
        'url_shortener': ['templates/*.html'],
    },
    include_package_data=True,
    install_requires=install_requires,
    license=_license,
    classifiers=(
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Internet :: WWW/HTTP :: Site Management :: Link Checking'
    ),
    keywords='url-shortener',
    tests_require=tests_require,
    extras_require={
        'test': tests_require
    },
)
