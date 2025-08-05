import logging

from playwright.sync_api import sync_playwright

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
        self.playwright = None
        self.current_url = None

    def __del__(self):
        self.quit()

    # chrome start
    def start(self):
        try:
            if self.driver is not None: return

            # Playwright 실행
            self.playwright = sync_playwright().start()
            # Chromium 브라우저 실행 (headless 모드)
            self.driver = self.playwright.chromium.launch(headless=True)

        except Exception as ex:
            logging.error("ChromeDrv failed to start.", ex)
            exit(1)

    # chrome quit
    def quit(self):
        if self.driver is None: return
        self.driver.close()
        self.playwright.stop()
        self.playwright = None
        self.driver = None

    # get url and return page
    def get(self, url):
        try:
            # 새 브라우저 컨텍스트 생성 (User-Agent, Locale 설정)
            context = self.driver.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                locale='en-US'
            )

            # 새 페이지 열기
            page = context.new_page()

            # Stealth 우회 스크립트 삽입
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.navigator.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            """)

            # 페이지 이동
            page.goto(url)
            page.wait_for_timeout(5000)  # 5초 대기

            res = page.content()
            return { "url": self.driver.current_url, "body": res }
        except Exception as ex:
            logging.info("chrome request error : {0}".format(url), ex)
            return None
        return res
