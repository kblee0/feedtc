import logging
import random
import time

from playwright.sync_api import sync_playwright

class ChromeDrv:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(ChromeDrv, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return

        self.__initialized = True
        self.driver = None
        self.playwright = None

    def __del__(self):
        self.quit()

    # ------------------------------------------------------------------
    # Browser Start
    # ------------------------------------------------------------------
    def start(self):
        if self.driver is not None:
            return

        try:
            self.playwright = sync_playwright().start()

            self.driver = self.playwright.chromium.launch(
                channel="chrome",      # 실제 Chrome 사용
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-web-security",
                ]
            )

        except Exception:
            logging.exception("ChromeDrv failed to start")
            raise

    # ------------------------------------------------------------------
    # Browser Stop
    # ------------------------------------------------------------------
    def quit(self):
        try:
            if self.driver:
                self.driver.close()
        except:
            pass

        try:
            if self.playwright:
                self.playwright.stop()
        except:
            pass

        self.driver = None
        self.playwright = None

    # ------------------------------------------------------------------
    # URL Open
    # ------------------------------------------------------------------
    def get(self, url):
        max_retry = 3
        for attempt in range(max_retry + 1):
            context = None
            try:
                self.start()
                context = self.driver.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/138.0.0.0 Safari/537.36"
                    ),
                    locale="ko-KR",
                    timezone_id="Asia/Seoul",
                    ignore_https_errors=True,
                    viewport={
                        "width": 1920,
                        "height": 1080
                    }
                )
                page = context.new_page()

                # webdriver 제거
                page.add_init_script("""
                    Object.defineProperty(
                        navigator,
                        'webdriver',
                        {
                            get: () => undefined
                        }
                    );
                    window.chrome = {
                        runtime: {}
                    };
                    Object.defineProperty(
                        navigator,
                        'languages',
                        {
                            get: () => ['ko-KR', 'ko', 'en-US', 'en']
                        }
                    );
                    Object.defineProperty(
                        navigator,
                        'plugins',
                        {
                            get: () => [1,2,3,4,5]
                        }
                    );
                """)

                page.set_default_navigation_timeout(60000)
                page.set_default_timeout(60000)

                logging.info( "Requesting (%s/%s): %s", attempt + 1, max_retry + 1, url)
                response = page.goto( url, wait_until="domcontentloaded", timeout=60000)

                if response:
                    logging.info( "Status=%s URL=%s", response.status, page.url)

                page.wait_for_timeout(2000)
                body = page.content()
                result = { "url": page.url, "body": body }
                context.close()

                return result

            except Exception as ex:
                logging.exception( "chrome request error : %s", url)
                if context:
                    try:
                        context.close()
                    except:
                        pass

                error_msg = str(ex).lower()

                retry_errors = [
                    "err_connection_reset",
                    "err_connection_closed",
                    "err_connection_timed_out",
                    "timeout",
                    "net::"
                ]
                if any(x in error_msg for x in retry_errors):
                    if attempt < max_retry:
                        wait_sec = ( (2 ** (attempt + 1)) + random.uniform(0.5, 1.5))
                        logging.info( "%.2f초 후 재시도 (%s/%s)", wait_sec, attempt + 1, max_retry)
                        time.sleep(wait_sec)
                        continue
                return None
        return None
