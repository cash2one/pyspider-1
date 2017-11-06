#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2012-11-09 14:39:57
# Modify: 2015-12-01 14:15:22

import mimetypes

import six
import shlex
from six.moves.urllib.parse import urlparse, urlunparse, ParseResult, urlencode, unquote, quote, parse_qsl
from requests.models import RequestEncodingMixin
import os
import pyurl
import posixpath

# constains
_ALWAYS_SAFE_BYTES = (b'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                      b'abcdefghijklmnopqrstuvwxyz'
                      b'0123456789' b'_.-')
_reserved = b';/?:@&=+$|,#' # RFC 3986 (Generic Syntax)
_unreserved_marks = b"-_.!~*'()" # RFC 3986 sec 2.3
_safe_chars = _ALWAYS_SAFE_BYTES + b'%' + _reserved + _unreserved_marks


lib_dir = os.path.dirname(os.path.realpath(__file__))

# def get_domain(url):
#     """get domain of given url"""
#     temp_url = url.split("#")[0]
#     temp_url = temp_url.split("?")[0]
#
#     cmd = "echo %s | %s domain" % (temp_url, os.path.join(lib_dir, "get_maindomain"))
#     ret_code, output = commands.getstatusoutput(cmd)
#     if ret_code != 0:
#         return False, None
#     return True, output


def get_domain(url):
    try:
        pyurl.setMultiSchemes(1)
        pyurl.normalizeUrl(url)
        domain = pyurl.getMainDomain(url)
    except Exception as e:
        domain = ''
    return domain

#def get_domain(url):
#    host = urlparse(url).netloc.lower()
#    if not host:
#        return ''
#    host = host.split('.')
#    if len(host) > 3:
#        return '.'.join(host[-3:])
#    if len(host) == 3:
#        return host[1] + '.' + host[2]
#    return '.'.join(host)


def get_content_type(filename):
    """Guessing file type by filename"""
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


_encode_params = RequestEncodingMixin._encode_params


def _encode_multipart_formdata(fields, files):
    body, content_type = RequestEncodingMixin._encode_files(files, fields)
    return content_type, body


def url_is_from_any_domain(url, domains):
    """Return True if the url belongs to any of the given domains"""
    host = urlparse(url).netloc.lower()
    if not host:
        return False
    domains = [d.lower() for d in domains]
    return any((host == d) or (host.endswith('.%s' % d)) for d in domains)


def url_has_any_extension(url, extensions):
    return posixpath.splitext(urlparse(url).path)[1].lower() in extensions


def add_http_if_no_scheme(url):
    """Add http as the default scheme if it is missing from the url."""
    if url.startswith('//'):
        url = 'http:' + url
        return url
    parser = urlparse(url)
    if not parser.scheme or not parser.netloc:
        url = 'http://' + url
    return url


def unicode_to_str(text, encoding='utf-8', errors='strict'):
    """encoding unicode by given encoding"""
    if isinstance(text, unicode):
        return text.encode(encoding, errors)
    elif isinstance(text, six.string_types):
        return text
    else:
        raise TypeError('unicode_to_str receive a unicode or str, got %s' % type(text).__name__)

def _build_url(url, _params, keep_blank_values=True, keep_fragment=False, encoding='utf-8'):
    """Build the actual URL to use.
    And then anonicalize the given url by applying the following procedures:
    - percent encode paths and query arguments. non-ASCII characters are
      percent-encoded using UTF-8 (RFC-3986)
    - normalize all spaces (in query arguments) '+' (plus symbol)
    - normalize percent encodings case (%2f -> %2F)
    - remove query arguments with blank values (unless keep_blank_values is True)
    - remove fragments (unless keep_fragments is True)
    """

    # Support for unicode domain names and paths.
    scheme, netloc, path, params, query, fragment = urlparse(unicode_to_str(url, encoding=encoding))
    netloc = netloc.encode('idna').decode(encoding)
    key_values = parse_qsl(query, keep_blank_values)

    query = urlencode(key_values)
    path = safe_url_string(_unquotepath(path)) or '/'
    fragment = fragment if keep_fragment else ''

    enc_params = _encode_params(_params)
    if enc_params:
        if query:
            query = '%s&%s' % (query, enc_params)
        else:
            query = enc_params
    url = (urlunparse([scheme, netloc, path, params, query, fragment]))
    return url


def _unquotepath(path):
    """unquote path normalize percent"""
    for reserved in ('2f', '2F', '3f', '3F'):
        path = path.replace('%' + reserved, '%25' + reserved.upper())
    return unquote(path)


def safe_url_string(url, encoding='utf8'):
    """save encode and quote url"""
    s = unicode_to_str(url, encoding)
    return quote(s, _safe_chars)


def quote_chinese(url, encoding="utf-8"):
    """Quote non-ascii characters"""
    if isinstance(url, six.text_type):
        return quote_chinese(url.encode(encoding))
    if six.PY3:
        res = [six.int2byte(b).decode('latin-1') if b < 128 else '%%%02X' % b for b in url]
    else:
        res = [b if ord(b) < 128 else '%%%02X' % ord(b) for b in url]
    return "".join(res)


def curl_to_arguments(curl):
    kwargs = {}
    headers = {}
    command = None
    urls = []
    current_opt = None

    for part in shlex.split(curl):
        if command is None:
            # curl
            command = part
        elif not part.startswith('-') and not current_opt:
            # waiting for url
            urls.append(part)
        elif current_opt is None and part.startswith('-'):
            # flags
            if part == '--compressed':
                kwargs['use_gzip'] = True
            else:
                current_opt = part
        else:
            # option
            if current_opt is None:
                raise TypeError('Unknow curl argument: %s' % part)
            elif current_opt in ('-H', '--header'):
                key_value = part.split(':', 1)
                if len(key_value) == 2:
                    key, value = key_value
                headers[key.strip()] = value.strip()
            elif current_opt in ('-d', '--data'):
                kwargs['data'] = part
            elif current_opt in ('--data-binary'):
                if part[0] == '$':
                    part = part[1:]
                kwargs['data'] = part
            elif current_opt in ('-X', '--request'):
                kwargs['method'] = part
            else:
                raise TypeError('Unknow curl option: %s' % current_opt)
            current_opt = None

    if not urls:
        raise TypeError('curl: no URL specified!')
    if current_opt:
        raise TypeError('Unknow curl option: %s' % current_opt)

    kwargs['urls'] = urls
    if headers:
        kwargs['headers'] = headers

    return kwargs

if __name__ == '__main__':
    '''test'''
    print _build_url('http://www.example.com/do?&a=1', None)
    print _build_url('http://www.example.com/do?q=a%20space&a=1', None)
    print _build_url('http://www.example.com/a do?a=1', None)
    print _build_url('http://www.example.com/a %20do?a=1', None)
    print get_domain('www.baidu.com')
