import logging
import re

class FeedItem:
    def __init__(self, title = '', link = '', downlaod_dir = None):
        self.title = ''
        self.link = link
        self.match = None
        self.series_name = ''
        self.download_dir = downlaod_dir
        self.set_title(title)

    def set_title(self, title):
        self.title = title
        regex = r"^(.+)[._](E\d+)[._]((\d{6,8})[._])?"
        matches = re.search(regex, title)
        if matches:
            if matches.group(4) is None:
                self.series_name = re.sub('[ -]', '', matches.group(1)) + "." + matches.group(2)
            else:
                self.series_name = re.sub('[ -]', '', matches.group(1)) + "." + matches.group(4)

    def set_download_dir(self, download_dir):
        self.download_dir = download_dir

    def check_filter(self, filters, debug=False):
        if not filters:
            return False
        for pattern in filters:
            match = re.search(pattern, self.title)
            if debug: logging.info("title: {}, pattern: {}, match: {}".format(self.title, pattern, match))
            if match:
                self.match = match
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
