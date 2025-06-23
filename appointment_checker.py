import sys
import time
import os
import requests
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

def send_telegram_message(message, bot_token=None, chat_id=None):
    bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("Telegram credentials not set.")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    if len(message) > 4000:
        message = message[:4000] + "\n... (truncated)"
    formatted_message = (
        f"🤖 *Appointment Checker*\n\n"
        f"{message}\n\n"
        f"📅 Time: `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`"
    )
    payload = {
        "chat_id": chat_id,
        "text": formatted_message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Telegram response: {response.status_code}")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def perform_actions():
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/chromium-browser'
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    driver = None

    print("Starting appointment check...")

    try:
        driver = webdriver.Chrome(options=chrome_options)

        driver.get("https://appointment.bmeia.gv.at")
        time.sleep(3)
        print("Current URL:", driver.current_url)
        print("Page Title:", driver.title)

        print("Selecting Office...")
        dropdown = Select(driver.find_element(By.ID, "Office"))
        dropdown.select_by_visible_text("KAIRO")
        submit_button = driver.find_element(By.NAME, "Command")
        submit_button.click()
        print("Submitted office selection.")
        print("Current URL:", driver.current_url)
        print("Page Title:", driver.title)

        time.sleep(2)

        # Check for error message
        error_message = None
        try:
            error_elem = driver.find_element(By.CSS_SELECTOR, "p.message-error")
            error_message = error_elem.text.strip()
        except Exception:
            error_message = None

        # Check if appointment heading appears
        appointment_heading = False
        try:
            headings = driver.find_elements(By.TAG_NAME, "h2")
            for h in headings:
                if "Appointments available" in h.text:
                    appointment_heading = True
                    break
        except Exception:
            appointment_heading = False

        # Check if calendar dropdown is present
        calendar_present = False
        try:
            driver.find_element(By.ID, "CalendarId")
            calendar_present = True
        except Exception:
            calendar_present = False

        # Decision logic
        if appointment_heading or calendar_present:
            send_telegram_message("🎉 *Possible appointments found!*\nCheck the website immediately.")
            print("Possible appointments found (heading or calendar present).")
            return

        if error_message:
            send_telegram_message("❌ No appointments found.")
            print("No appointments found. Exiting early.")
            return

        # If neither heading, calendar, nor error message, site may have changed
        send_telegram_message("❌ No calendar, no error, no appointments heading -- site may have changed.")
        print("No calendar, no error, no heading. Exiting.")
        return

    except Exception as e:
        tb = traceback.format_exc()
        page_source = ""
        current_url = ""
        title = ""
        if driver:
            try:
                current_url = driver.current_url
                title = driver.title
                page_source = driver.page_source
                if len(page_source) > 1500:
                    page_source = page_source[:1500] + "\n... (truncated)"
            except Exception:
                pass
        send_telegram_message(
            f"❗ Error occurred: {type(e).__name__}: {e}\n\n"
            f"Traceback (last lines):\n{tb[-1000:]}\n"
            f"URL: {current_url}\nTitle: {title}\n"
            f"Page source snippet:\n{page_source}"
        )
        print(f"An error occurred: {e}\n{tb}")
    finally:
        time.sleep(2)
        if driver:
            driver.quit()

if __name__ == "__main__":
    print(f"Script started at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    perform_actions()