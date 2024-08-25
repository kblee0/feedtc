import logging
import transmissionrpc

class Transmission:
    def __init__(self, config):
        self.config = config
        if config.get('add_paused'):
            self.add_paused= config['add_paused']
        else:
            self.add_paused = False
        # Connecting to Transmission
        try:
            if not config.get('host'):
                config.host = 'localhost'
            if not config.get('port'):
                config.port = 9091
            self.client = transmissionrpc.Client(
                config['host'],
                port=config['port'],
                user=config['username'],
                password=config['password'])

        except transmissionrpc.error.TransmissionError as ex:
            logging.error("TransmissionError: ", ex)
            exit(1)
        except Exception as ex:
            logging.error("Exception: ", ex)
            exit(1)

    def add_torrent(self, torrent_url, download_dir=None):
        if download_dir is None:
            self.client.add_torrent(torrent_url, paused=self.add_paused)
        else:
            self.client.add_torrent(torrent_url, download_dir=download_dir, paused=self.add_paused)