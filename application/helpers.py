#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from application import app, authomatic
from flask.ext.login import current_user

# encrypt and decrypt
from Crypto.Cipher import AES
from Crypto import Random

# is_safe_url
from urlparse import urlparse, urljoin
from flask import request, url_for, session

# based on https://gist.github.com/gruber/249502
# from http://daringfireball.net/2010/07/improved_regex_for_matching_urls
# modified to exclude urls within anchor tags
URL_REGEX = re.compile(
    r'(?!<a[^>]*?>)'
    r'(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.]'
    r'[a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\('
    r'([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))'
    r'(?![^<]*?</a>)'
)


def add_tags_to_urls(value):
    ''' adds anchor tags to urls in text '''
    return URL_REGEX.sub(r'<a href="\g<1>" target="_blank">\g<1></a>', value)


# http://flask.pocoo.org/snippets/62/
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


# encrypt_string & decrypt_string: used to encrypt url so users can't guess eachother URL
#TODO: This was a bad idea, it can be incremented easily and past URLs work after the request is deleted. It needs to be combined with the user ID + row_id at least.
#        Usually a separate database is used to keep track of the encoded URLS, this allows a random string to be used.
#        I wanted to avoid this because Heroku charges you when your database goes over like 10k rows.
def encrypt_string(value):
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(app.config['ENCRYPTION_KEY'], AES.MODE_CFB, iv)
    msg = iv + cipher.encrypt(bytes(value))
    return msg.encode("hex")


def decrypt_string(value):
    try:
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(app.config['ENCRYPTION_KEY'], AES.MODE_CFB, iv)
        return cipher.decrypt(value.decode("hex"))[len(iv):]
    except:
        return False


def credentials(name='credentials'):
    # if you're getting keyerrors here, you need to check is_valid_credentials and redirect to login with next=request.url
    return authomatic.credentials(session[name])


def is_valid_credentials(name='credentials'):
    return current_user.is_authenticated() and session.get(name) and credentials(name).valid
