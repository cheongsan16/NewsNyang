import os
import asyncio
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import telegram
from telegram.constants import ParseMode

# GitHub Secrets에서 보안 정보를 가져옵니다.
TELEGRAM_TOKEN = os.environ.get('8932667103:AAGu3h_8ducSiyJUQjI38QQ4gw6eNAdqjbA')
CHAT_ID = os.environ.get('7767161293')

def scrape_today_meals():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # 크롤링할 부산대학교 기숙사 식단표 URL
        url = 'https://dorm.pusan.ac.kr/pdorm/page?menuCD=000000000000561' 
        driver.get(url)
        
        # 자유관 탭(mealPlanTab_3) 클릭
        wait = WebDriverWait(driver, 10)
        tab3 = wait.until(EC.element_to_be_clickable((By.ID, 'mealPlanTab_3')))
        tab3.click()

        time.sleep(2) # 로딩 대기
        
        # 오늘 날짜 (YYYY-MM-DD)
        today_str = datetime.now().strftime("%Y-%m-%d")
        rows = driver.find_elements(By.CSS_SELECTOR, "#mealPlanTable tr")
        
        result_message = "📋 <b>자유관 오늘의 메뉴</b>\n"
        current_date_str = ""
        is_today = False
        
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            
            # 날짜 정보가 있는 첫 번째 셀(td가 3개)
            if len(cells) == 3:
                date_text = cells[0].text
                current_date_str = date_text.replace('\n', ' ')
                
                if today_str in date_text:
                    is_today = True
                    result_message += f"\n▶️ <b>{current_date_str}</b>\n"
                else:
                    is_today = False
                    
                meal_type = cells[1].text
                menu = cells[2].text
                
            # 날짜 정보 없이 분류, 메뉴만 있는 셀(td가 2개)
            elif len(cells) == 2 and current_date_str:
                meal_type = cells[0].text
                menu = cells[1].text
                
            # 오늘 날짜이면서 중식 또는 석식일 때만 추가
            if is_today and meal_type in ['중식', '석식']:
                if meal_type == '중식':
                    result_message += f"\n☀️ <b>{meal_type}</b>\n{menu}\n"
                elif meal_type == '석식':
                    result_message += f"\n🌙 <b>{meal_type}</b>\n{menu}\n"
                
        if result_message.count('\n') <= 1:
            return "오늘의 중식/석식 식단 정보가 없습니다."
            
        return result_message.strip()
        
    except Exception as e:
        return f"크롤링 중 오류가 발생했습니다: {str(e)}"
    finally:
        driver.quit()

async def send_message(text):
    # 넉넉한 타임아웃과 재시도 로직 적용
    request = telegram.request.HTTPXRequest(connect_timeout=20.0, read_timeout=20.0)
    bot = telegram.Bot(token=TELEGRAM_TOKEN, request=request)
    
    for attempt in range(3):
        try:
            await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode=ParseMode.HTML)
            print("메시지 전송 성공!")
            return
        except Exception as e:
            print(f"네트워크 오류 재시도 {attempt + 1}/3: {e}")
            await asyncio.sleep(5)
    print("메시지 전송 최종 실패")

async def main():
    print("식단 크롤링 시작...")
    meal_data = scrape_today_meals()
    await send_message(meal_data)

if __name__ == '__main__':
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
