import html
import logging
import re
import urllib.parse
from pathlib import PurePath
from typing import Match


class FeedItem:
    def __init__(self, title = '', link = '', download_dir = None):
        self.title = ''
        self.link = link
        self.match = None
        self.series_name = ''
        self.download_dir = download_dir
        self.set_title(title)

    def set_title(self, title:str):
        self.title = title
        self.series_name = ''
        return self

    def set_series_name(self, title_pattern:str):
        regex = rf"({re.escape(title_pattern)}).*\.(S\d+E\d+|\d{{6,8}})\."
        matches = re.search(regex, self.title)
        if matches:
            self.series_name = re.sub('[ -]', '', matches.group(1)) + "." + matches.group(2)
            return self

        regex = r"^(.+?)(?:\..+)?\.(S\d+E\d+|\d{6,8})\."
        matches = re.search(regex, self.title)
        if matches:
            self.series_name = re.sub('[ -]', '', matches.group(1)) + "." + matches.group(2)

        return self

    def _formatting_with_match(self, format_str:str, match:Match):
        m = [match.group()]
        for group_no in range(0, len(match.groups())):
            group_no = group_no + 1
            m.append(match.group(group_no))

        return format_str.format(*m)

    def set_title_by_match(self, format_str, match:Match):
        title = self._formatting_with_match(format_str,match)

        # HTML tag remove
        cleaner = re.compile('<.*?>')
        title = re.sub(cleaner, '', title)

        self.set_title(html.unescape(title))
        return self

    def set_link_by_match(self, format_str, match:Match, referer_url):
        link = self._formatting_with_match(format_str,match)

        linkpart = urllib.parse.urlparse(link)
        if linkpart.scheme == '':
            refererpart = urllib.parse.urlparse(referer_url)
            link = refererpart.scheme + '://' + refererpart.netloc + link

        self.link = html.unescape(link.strip())
        return self

    def set_download_dir(self, download_dir):
        sub_dir = self.match and self.match.groupdict().get('dir')
        if sub_dir:
            self.download_dir = str(PurePath(download_dir, sub_dir))
        else:
            self.download_dir = str(PurePath(download_dir))

    def check_filter(self, filters, debug=False):
        if not filters:
            return False
        for pattern in filters:
            # 입력된 패턴으로 체크
            match = re.search(pattern, self.title)
            if debug: logging.info("title: {}, pattern: {}, match: {}".format(self.title, pattern, match))
            if match:
                self.match = match
                self.set_series_name(pattern)
                return True
            # 입력된 패턴에서 공백으로 제거하고 체크
            match = re.search(pattern, self.title.replace(' ', ''))
            if debug: logging.info("title: {}, pattern: {}, match: {}".format(self.title, pattern, match))
            if match:
                self.match = match
                self.set_series_name(pattern)
                return True
        self.match = None
        return False

    def __repr__(self):
        return "{'title': '{}', 'link': '{}', 'match': {}, 'series_name': '{}'}".format(
            self.title,
            self.link,
            self.match.group(0) if self.match else "None",
            self.series_name)

    def __str__(self):
        return ("""
----------------------------------------------------------------------
Title       : {}
Link        : {}
Match       : {}
Series name : {}
----------------------------------------------------------------------
""".format(self.title, self.link, (self.match.group(0) if self.match else "None"), self.series_name))
