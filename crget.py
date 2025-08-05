import sys

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

url = sys.argv[1]

# Chrome 옵션 설정
options = uc.ChromeOptions()

# Headless "new" 모드 (중요)
options.add_argument('--headless=new')

# 기타 탐지 우회 옵션들
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# Chrome 실행
driver = uc.Chrome(options=options)

print("GET: " + url)
# 접속 (브라우저 지문 확인 페이지 예시)
driver.get(url)  # 봇 탐지 페이지

# 페이지 내 텍스트 출력 (봇 탐지 여부)
print(driver.page_source)

driver.quit()
