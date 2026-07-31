import logging
import transmission_rpc

class Transmission:
    def __init__(self, config):
        self.config = config
        self.add_paused = config.get('add_paused', False)

        try:
            self.client = transmission_rpc.Client(
                host=config.get('host', 'localhost'),
                protocol=config.get('protocol', 'http'),
                port=config.get('port', 9091),
                username=config['username'],
                password=config['password']
            )

        except transmission_rpc.TransmissionError as ex:
            logging.error("TransmissionError: %s", ex)
            raise
        except Exception as ex:
            logging.error("Exception: %s", ex)
            raise

    def add_torrent(self, torrent_url, download_dir=None):
        if download_dir is None:
            self.client.add_torrent(
                torrent_url,
                paused=self.add_paused
            )
        else:
            self.client.add_torrent(
                torrent_url,
                download_dir=download_dir,
                paused=self.add_paused
            )