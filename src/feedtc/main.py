import argparse
import logging
import sys

from feedtc.task.feed_tc import FeedTc


def main():
    # arg parse configuration and argument definitions
    parser = argparse.ArgumentParser(description='Reads RSS/Atom Feeds and add torrents to Transmission')
    parser.add_argument('--config-file',
                        default='feedtc.yml',
                        metavar='<configfile path>',
                        help='The config file. default is feedtc.yml')
    parser.add_argument('--database',
                        default='feedtc.db',
                        metavar='<database location >',
                        help='download hist database location')
    parser.add_argument('--log-file',
                        default=None,
                        metavar='<logfile path>',
                        help='The logging file, if not specified, prints to output')
    parser.add_argument('--log-level',
                        default='info',
                        metavar='<log level>',
                        help='critical, error, warning, info, debug')
    parser.add_argument('--url',
                        default=None,
                        metavar='<url>',
                        help='Specify the url to download the torrent from')

    # parse the arguments
    args = parser.parse_args()

    log_level = getattr(logging, args.log_level.upper())
    if args.log_file:
        logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', level=log_level, filename=args.log_file)
    else:
        logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', level=log_level, stream=sys.stdout)

    FeedTc(args.config_file, args.database).run_job(args.url)
