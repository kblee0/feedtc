import logging

from pyvirtualdisplay import Display
from selenium import webdriver

class ChromeDrv:
    __instance = None
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(ChromeDrv, cls).__new__(cls)
            cls.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized: return
        self.__initialized = True
        self.display = Display(visible=False, size=(1920, 1080))
        self.display.start()
        self.driver = None

    def __del__(self):
        self.quit()
        self.display.stop()

    # chrome start
    def __enter__(self):
        self.start()
        return self

    # chrome quit
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()

    # chrome start
    def start(self):
        try:
            if self.driver is None: self.driver = webdriver.Chrome()
        except Exception as ex:
            logging.error("ChromeDrv failed to start.", ex)
            exit(1)

    # chrome quit
    def quit(self):
        if self.driver is None: return
        self.driver.quit()
        self.driver = None

    # get url and return page
    def get(self, url):
        self.start()
        try:
            self.driver.get(url)
            self.driver.implicitly_wait(3)
            res = self.driver.page_source
        except Exception as ex:
            logging.info("chrome request error : {0}".format(url), ex)
            return None
        return res
