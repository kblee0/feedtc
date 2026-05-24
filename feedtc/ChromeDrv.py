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
        max_retry = 2

        for attempt in range(max_retry+1):
            context = None
            try:
                self.start()

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

                # [보완 1] 불필요한 광고/트래킹 리소스 차단으로 네트워크 부하 감소 (선택 사항)
                page.route("**/*.{png,jpg,jpeg,gif,webp,mp4,css,woff,woff2}", lambda route: route.abort())

                # [보완 2] wait_until을 "commit"(HTML 수신 시작)으로 변경하여 무거운 광고 로딩 대기 회피
                page.goto(url, timeout=45000, wait_until="commit")

                # [보완 3] networkidle 대신 기본 DOM 로드만 확인 (광고 스트리밍 등으로 인한 무한 대기 방지)
                page.wait_for_load_state('domcontentloaded')

                # 페이지 이동
                # page.goto(url, timeout=60000, wait_until="domcontentloaded")
                # page.wait_for_load_state('networkidle') # 네트워크 idle 상태까지 대기
                res = page.content()

                # 정상 처리 시 context 닫고 반환
                context.close()
                return { "url": page.url, "body": res }
            except Exception as ex:
                logging.exception("chrome request error : %s", url)
                if context:
                    try: context.close() # 에러 시에도 안전하게 컨텍스트 종료
                    except: pass
                if attempt < max_retry:
                    wait_sec = (2 ** (attempt + 1)) + random.uniform(0.5, 1.5)
                    logging.info("{}초 후 다시 시도합니다. ({}/{})".format(wait_sec, attempt + 1, max_retry))
                    time.sleep(wait_sec)
                    continue
                return None
        return None
