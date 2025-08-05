import sys

from playwright.sync_api import sync_playwright

# pip install playwright
# playwright install chromium

url = sys.argv[1]

# Playwright 실행
playwright = sync_playwright().start()

# Chromium 브라우저 실행 (headless 모드)
browser = playwright.chromium.launch(headless=True)

# 새 브라우저 컨텍스트 생성 (User-Agent, Locale 설정)
context = browser.new_context(
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

# 페이지 소스 출력
print(page.content())

# 리소스 정리
browser.close()
playwright.stop()
