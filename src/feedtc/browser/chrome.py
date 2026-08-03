import random
import logging
import random
import time
from html import escape
from pathlib import Path

from playwright.sync_api import sync_playwright


class Chrome:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(Chrome, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    @classmethod
    def get_instance(cls):
        return cls()

    def __init__(self):
        if self.__initialized:
            return

        self.__initialized = True
        self.driver = None
        self.playwright = None

    # ------------------------------------------------------------------
    # Browser Start
    # ------------------------------------------------------------------
    def start(self):
        if self.driver is not None:
            return

        try:
            self.playwright = sync_playwright().start()

            self.driver = self.playwright.chromium.launch(
                channel="chrome",
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
        except Exception:
            pass

        try:
            if self.playwright:
                self.playwright.stop()
        except Exception:
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
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                    locale="ko-KR",
                    timezone_id="Asia/Seoul",
                    ignore_https_errors=True,
                    viewport={"width": 1920, "height": 1080}
                )

                page = context.new_page()
                self._setup_page(page)

                logging.info("Requesting (%s/%s): %s", attempt + 1, max_retry + 1, url)
                response = page.goto(url, wait_until="domcontentloaded", timeout=60000)
                if response:
                    logging.info("Status=%s URL=%s", response.status, page.url)
                page.wait_for_timeout(2000)

                result = {
                    "url": page.url,
                    "body": page.content()
                }
                context.close()
                return result

            except Exception as ex:
                logging.exception("chrome request error : %s", url)
                if context:
                    try:
                        context.close()
                    except Exception:
                        pass

                error_msg = str(ex).lower()

                retry_errors = [
                    "err_connection_reset",
                    "err_connection_closed",
                    "err_connection_timed_out",
                    "timeout",
                    "net::"
                ]
                if any(x in error_msg for x in retry_errors) and attempt < max_retry:
                    wait_sec = (2 ** (attempt + 1)) + random.uniform(0.5, 1.5)
                    logging.info("%.2f초 후 재시도 (%s/%s)", wait_sec, attempt + 1, max_retry)
                    time.sleep(wait_sec)
                    continue
                return None
        return None

    # ------------------------------------------------------------------
    # Context 생성
    # ------------------------------------------------------------------
    def _new_context(self):
        self.start()

        context = self.driver.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            ignore_https_errors=True,
            viewport={"width": 1920, "height": 1080}
        )
        return context

    # ------------------------------------------------------------------
    # Anti webdriver
    # ------------------------------------------------------------------
    def _setup_page(self, page):
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
                    get: () => [1, 2, 3, 4, 5]
                }
            );
        """)

        page.set_default_navigation_timeout(60000)
        page.set_default_timeout(60000)

    def download_images(self, images):
        if not images:
            logging.warning("다운로드할 이미지가 없습니다.")
            return False

        max_retry = 3

        for attempt in range(max_retry + 1):
            context = None

            try:
                context = self._new_context()

                page = context.new_page()
                self._setup_page(page)

                total = len(images)

                # ----------------------------------------------------------
                # 이미 다운로드된 이미지 제외
                # ----------------------------------------------------------
                pending_images = []

                for index, image in enumerate(images, 1):
                    file_path = Path(image["file_path"])
                    file_path.parent.mkdir(parents=True, exist_ok=True)

                    if file_path.exists() and file_path.stat().st_size > 0:
                        logging.warn("[%03d/%03d] 이미 존재: %s",index, total, file_path.name)
                        continue

                    pending_images.append({
                        "index": index,
                        "url": image["url"],
                        "file_path": file_path,
                    })

                # ----------------------------------------------------------
                # 다운로드할 이미지가 없는 경우
                # ----------------------------------------------------------
                if not pending_images:
                    logging.info("모든 이미지가 이미 존재합니다.")
                    context.close()
                    return True

                # ----------------------------------------------------------
                # URL -> 이미지 정보
                # ----------------------------------------------------------
                image_map = {image["url"]: image for image in pending_images}
                downloaded = set()

                # ----------------------------------------------------------
                # Chrome response 이벤트
                # ----------------------------------------------------------
                def on_response(response):
                    try:
                        response_url = response.url
                        if response_url not in image_map:
                            return
                        if response_url in downloaded:
                            return
                        if not response.ok:
                            logging.warning("이미지 응답 실패: status=%s url=%s", response.status, response_url)
                            return

                        body = response.body()
                        if not body:
                            logging.warning("이미지 데이터가 비어있습니다: %s", response_url)
                            return

                        image = image_map[response_url]
                        file_path = image["file_path"]

                        file_path.write_bytes(body)
                        downloaded.add(response_url)

                        logging.debug("[%03d/%03d] 완료: %s (%,d bytes)", image['index'], total, file_path.name, len(body))
                    except Exception:
                        logging.exception("Image response error: %s", response.url)

                page.on("response", on_response)

                # ----------------------------------------------------------
                # 다운로드 대상만 HTML 생성
                # ----------------------------------------------------------
                html_images = "\n".join(
                    f'<img src="{escape(image["url"], quote=True)}" loading="eager">'
                    for image in pending_images
                )

                html = f'<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>{html_images}</body></html>'

                logging.info("이미지 다운로드 시작: %d/%d", len(pending_images), total)

                # ----------------------------------------------------------
                # 이미지 HTML 로딩
                # ----------------------------------------------------------
                page.set_content(html, wait_until="domcontentloaded", timeout=60000)

                # ----------------------------------------------------------
                # 이미지 다운로드 대기
                # ----------------------------------------------------------
                timeout = 60
                check_interval = 0.2
                elapsed = 0
                target = len(pending_images)

                while elapsed < timeout:
                    loaded = len(downloaded)

                    if loaded >= target:
                        logging.info("모든 이미지 다운로드 완료: %d/%d", loaded, target)
                        break

                    page.wait_for_timeout(int(check_interval * 1000))
                    elapsed += check_interval
                else:
                    logging.warning("이미지 다운로드 대기시간 초과: %d/%d", len(downloaded), target)

                # ----------------------------------------------------------
                # 실패 이미지 확인
                # ----------------------------------------------------------
                failed = [image for image in pending_images if image["url"] not in downloaded]

                context.close()

                # ----------------------------------------------------------
                # 전체 성공
                # ----------------------------------------------------------
                if not failed:
                    logging.info("이미지 다운로드 완료: %d개", len(pending_images))
                    return True

                # ----------------------------------------------------------
                # 일부 실패
                # ----------------------------------------------------------
                logging.warning("이미지 다운로드 실패: %d/%d", len(failed), len(pending_images))

                if attempt < max_retry:
                    wait_sec = (2 ** (attempt + 1)) + random.uniform(0.5, 1.5)
                    logging.info("%.2f초 후 재시도 (%s/%s)", wait_sec, attempt + 1, max_retry)
                    time.sleep(wait_sec)
                    continue

                return False
            except Exception:
                logging.exception("Chrome image download error")
                if context:
                    try:
                        context.close()
                    except Exception:
                        pass
                if attempt < max_retry:
                    wait_sec = (2 ** (attempt + 1)) + random.uniform(0.5, 1.5)
                    logging.info("%.2f초 후 재시도 (%s/%s)", wait_sec, attempt + 1, max_retry)
                    time.sleep(wait_sec)
                    continue

                return False

        return False