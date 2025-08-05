import logging

import undetected_chromedriver as uc

class ChromeDrv:
    __instance = None
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(ChromeDrv, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized: return
        self.__initialized = True
        self.driver = None
        self.current_url = None

    def __del__(self):
        self.quit()

    # chrome start
    def start(self):
        try:
            if self.driver is not None: return
            # Chrome 옵션 설정
            options = uc.ChromeOptions()

            # Headless "new" 모드 (중요)
            options.add_argument('--headless=new')

            # 기타 탐지 우회 옵션들
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

            # Chrome 실행
            self.driver = uc.Chrome(options=options)
        except Exception as ex:
            logging.error("ChromeDrv failed to start.", ex)
            exit(1)

    # chrome quit
    def quit(self):
        if self.driver is None: return
        self.driver.service.stop()
        try:
            self.driver.quit()
        except OSError:
            pass
        self.driver = None

    # get url and return page
    def get(self, url):
        try:
            self.start()
            self.driver.get(url)
            res = self.driver.page_source
            return { "url": self.driver.current_url, "body": res }
        except Exception as ex:
            logging.info("chrome request error : {0}".format(url), ex)
            return None
        return res
