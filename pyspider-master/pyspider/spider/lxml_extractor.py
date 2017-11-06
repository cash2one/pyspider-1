"""
SGMLParser-based Link extractors
"""
import re
from urlparse import urlparse, urljoin
from pyspider.libs.url import (quote_chinese, _build_url, _encode_params, _encode_multipart_formdata,
                               curl_to_arguments, url_is_from_any_domain, add_http_if_no_scheme, url_has_any_extension)
from pyspider.libs.utils import arg_to_iter


_re_type = type(re.compile("", 0))

_matches = lambda url, regexs: any((r.search(url) for r in regexs))
_is_valid_url = lambda url: url.split('://', 1)[0] in set(['http', 'https', 'file'])

IGNORED_EXTENSIONS = [
    # images
    'mng', 'pct', 'bmp', 'gif', 'jpg', 'jpeg', 'png', 'pst', 'psp', 'tif',
    'tiff', 'ai', 'drw', 'dxf', 'eps', 'ps', 'svg',

    # audio
    'mp3', 'wma', 'ogg', 'wav', 'ra', 'aac', 'mid', 'au', 'aiff',

    # video
    '3gp', 'asf', 'asx', 'avi', 'mov', 'mp4', 'mpg', 'qt', 'rm', 'swf', 'wmv',
    'm4a',

    # office suites
    'xls', 'xlsx', 'ppt', 'pptx', 'doc', 'docx', 'odt', 'ods', 'odg', 'odp',

    # other
    'css', 'pdf', 'exe', 'bin', 'rss', 'zip', 'rar',
]

class LinkExtractor(object):

    def __init__(self, allow=(), deny=(), senior_allow={}, allow_domains=(), deny_domains=(), canonicalize=True, deny_extensions=None):
        self.allow = '|'.join(allow)
        self.deny = '|'.join(deny)
        self.allow_res = [re.compile(x) for x in arg_to_iter(allow)]
        self.deny_res = [re.compile(x) for x in arg_to_iter(deny)]
        self.allow_domains = set(arg_to_iter(allow_domains))
        self.deny_domains = set(arg_to_iter(deny_domains))
        self.senior_allow_res = dict()
        for k, v in senior_allow.iteritems():
            self.senior_allow_res[re.compile(k)] = re.compile(v)
        self.canonicalize = canonicalize
        if deny_extensions is None:
            deny_extensions = IGNORED_EXTENSIONS
        self.deny_extensions = set(['.' + e for e in deny_extensions])
        self._doc = None
        self._task_url = None

    def get_allow(self):
        return self.allow

    def get_deny(self):
        return self.deny

    def get_deny_domains(self):
        return '|'.join(self.deny_domains)

    def get_allow_domains(self):
        return '|'.join(self.allow_domains)

    def _extract_links(self):
        candidates = self._doc.xpath('//a')
        ret = []
        for each in candidates:
            if 'href' not in each.attrib or each.attrib['href'].lower().startswith('javascript')\
                    or each.attrib['href'].lower().startswith('mailto:'):
                    continue
            url = add_http_if_no_scheme(each.attrib['href'].strip())
            ret.append(url)
        return list(set(ret))

    def extract_links(self, response, task):
        self._doc = response.doc
        self._task_url = task['url']
        if self._doc is None or not self._task_url:
            return []
        if self._task_url.startswith('curl') or self._task_url.startswith('data'):
            return []
        links = self._extract_links()
        links = self._process_links(links)
        return links

    def _process_links(self, links):
        links = [x for x in links if self.link_allowed(x)]
        return links

    def is_senior_allow(self, url):
        """judge whether url match senior url patterns"""
        for src_pat, dir_pat in self.senior_allow_res.iteritems():
            if src_pat.match(self._task_url) and dir_pat.match(url):
                return True
        return False

    def link_allowed(self, url):
        allowed = _is_valid_url(url)
        if self.allow_res:
            allowed &= _matches(url, self.allow_res)
        if self.deny_res:
            allowed &= not _matches(url, self.deny_res)
        if self.senior_allow_res:
            allowed &= self.is_senior_allow(url)
        if self.allow_domains:
            allowed &= url_is_from_any_domain(url, self.allow_domains)
        if self.deny_domains:
            allowed &= not url_is_from_any_domain(url, self.deny_domains)
        if self.deny_extensions:
            allowed &= not url_has_any_extension(url, self.deny_extensions)
        return allowed

    def matches(self, url):
        if self.allow_domains and not url_is_from_any_domain(url, self.allow_domains):
            return False
        if self.deny_domains and url_is_from_any_domain(url, self.deny_domains):
            return False

        allowed = [regex.search(url) for regex in self.allow_res] if self.allow_res else [True]
        denied = [regex.search(url) for regex in self.deny_res] if self.deny_res else []
        return any(allowed) and not any(denied)
