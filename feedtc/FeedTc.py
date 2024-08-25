import base64
import html
import logging
import re
import urllib.parse
import urllib.request

import requests
import yaml

from feedtc.ChromeDrv import ChromeDrv
from feedtc.FeedItem import FeedItem
from feedtc.FeedItemHist import FeedItemHist
from feedtc.Transmission import Transmission


# Internal functions
def notify_message(message):
    url = 'http://localhost:18080/telegram/message'
    body = {
        "chat_name": "noticenter",
        "message": message,
        "async": True
    }
    requests.post(url=url, json=body)
    pass

def match_format(format_str, match):
    m = [match.group()]
    for group_no in range(0, len(match.groups())):
        group_no = group_no + 1
        m.append(match.group(group_no))

    return format_str.format(*m)

def remove_html_tag(content):
    cleaner = re.compile('<.*?>')
    cleantext = re.sub(cleaner, '', content)
    return cleantext

def get_magnet_url(url):
    res = ChromeDrv().get(url)

    if res is None:
        logging.error("Error reading feed \'{0}\': ".format(url))
        return None

    content = res

    regex = r"magnet_link\([\'\"](.*?)['\"]\)"
    matches = re.findall(regex, content, re.MULTILINE)
    if len(matches) > 0:
        logging.debug("magnet:?xt=urn:btih:" + matches[0])
        return "magnet:?xt=urn:btih:" + matches[0]

    regex = r"(magnet:.*?)['\"]"
    matches = re.findall(regex, content, re.MULTILINE)

    if len(matches) > 0:
        logging.debug(matches[0])
        return matches[0].replace("&amp;", "&").strip()

    return None

##########################################################
# FeedTc
##########################################################
class FeedTc:
    def __init__(self, config_file, database) :
        FeedItemHist().connect(database)

        with open(config_file, 'r', encoding='utf8') as stream:
            self.config = yaml.load(stream, Loader=yaml.FullLoader)

    def __del__(self):
        FeedItemHist().close()

    def run_job(self):
        for task_name in self.config['tasks']:
            FeedTcTask(self.config['tasks'][task_name]).run_task()

##########################################################
# FeedTcTask
##########################################################
class FeedTcTask:
    def __init__(self, task):
        self.task = task
        self.transmission = Transmission(task.get('transmission'))
        self.item_list = []
        self.result = {"accepted": 0, "rejected": 0, "undecided": 0, "failed": 0}

    def run_task(self):
        for input_item in self.task['inputs']:
            self.get_items_from_input(input_item)

        if len(self.item_list) == 0:
            first_input = self.task['inputs'][0]
            urls = first_input['html'] if isinstance(first_input.get('html'), list) else [first_input['html']]
            notify_message("feedtc list가 조회되지 않았습니다. 확인하세요.\n" + "\n".join(urls))
            exit(1)

        for item in self.item_list:
            self.process_item(item)
        logging.info("Feed transmission summary: {}".format(self.result))

    def process_item(self, item: FeedItem):
        logging.info("Item: " + item.title)

        accept_debug = False
        reject_debug = False
        # if item.title == 'TITLE': accept_debug = True

        item_status = {'accepted': False, 'rejected': False}
        for item_filter in self.task.get('filter'):
            if item.check_filter(item_filter.get('reject'), reject_debug):
                item_status['rejected'] = True
                break
            if item.check_filter(item_filter.get('accept'), accept_debug):
                item_status['accepted'] = True
                item.set_download_dir(item_filter.get('download_dir'))
                break

        # Check filter match
        if item_status['rejected']:
            logging.info("     +--> rejected")
            self.result['rejected'] += 1
            return
        if not item_status['accepted']:
            self.result['undecided'] += 1
            return

        # Accepted Case

        # already added item (check additem.txt) reject
        if FeedItemHist().count_item(item) > 0:
            logging.info("     +--> rejectd (added item)")
            self.result["rejected"] += 1
            return

        # add download
        try:
            self.download_item(item)
            self.result["accepted"] += 1
        except Exception as ex:
            logging.error("Error adding item \'{0}\': ".format(item.link), ex)
            self.result["failed"] += 1

    def download_item(self, item):
        if item.link[0:7] == "magnet:":
            torrent_url = item.link
        else:
            torrent_url = get_magnet_url(item.link)

        if not torrent_url:
            # Fix torrent url
            if item.link[-8:] != ".torrent":
                item.link = item.link + "&dummy=dummy.torrent"

            # read torrent data
            req = urllib.request.Request(item.link, data=None)
            response = urllib.request.urlopen(req)
            torrent = base64.b64encode(response.read())
            torrent_url = str(torrent)[2:-1]

        self.transmission.add_torrent(torrent_url, item.download_dir)
        logging.info("Adding Torrewnt: " + item.title + (("to "+ item.download_dir) if item.download_dir else ""))
        notify_message("Downloading: " + item.title)

        FeedItemHist().save_item(item)

    def get_items_from_input(self, src):
        urls = src['html'] if isinstance(src['html'], list) else [src['html']]

        for url in urls:
            logging.info("SITE URL: " + url)
            res = ChromeDrv().get(url)
            if res is None:
                notify_message("feedtc 오류가 발생했습니다.\nurl=" + url)
                exit(1)

            matches = re.finditer(src['item_pattern'], res.replace("\r", ""), re.MULTILINE | re.IGNORECASE)

            for match_num, match in enumerate(matches):
                title = remove_html_tag(match_format(src['item_title'], match))
                link = match_format(src['item_link'], match)

                linkpart = urllib.parse.urlparse(link)
                if linkpart.scheme == '':
                    srcpart = urllib.parse.urlparse(url)
                    link = srcpart.scheme + '://' + srcpart.netloc + link

                title = html.unescape(title.strip())
                link = html.unescape(link.strip())

                self.item_list.append(FeedItem(title, link))
