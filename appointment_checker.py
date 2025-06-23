import sys
import time
import logging
import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

# --- Telegram Notification ---
def send_telegram_message(message, bot_token=None, chat_id=None):
    bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("Telegram credentials not set.")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    # Limit message to Telegram's 4096 char max
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
    # Headless Chrome setup for GitHub Actions Linux
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=chrome_options)

    print("Starting appointment check...")

    try:
        driver.get("https://appointment.bmeia.gv.at")
        time.sleep(3)

        dropdown = Select(driver.find_element(By.ID, "Office"))
        dropdown.select_by_visible_text("KAIRO")
        submit_button = driver.find_element(By.NAME, "Command")
        submit_button.click()

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "CalendarId"))
        )

        calendar_dropdown = Select(driver.find_element(By.ID, "CalendarId"))
        options = [option.text.strip() for option in calendar_dropdown.options]
        current_count = len(options)
        expected_count = 9

        print(f"Available options ({current_count}):")
        for opt in options:
            print(f"- {opt}")

        # Telegram if changed
        if current_count != expected_count:
            send_telegram_message(
                f"⚠️ *Options changed*: found *{current_count}* vs expected *{expected_count}*"
            )
            return

        selected_option = None
        for opt in options:
            lower_opt = opt.lower()
            if "student" in lower_opt or "bachelor" in lower_opt:
                selected_option = opt
                break

        if selected_option:
            calendar_dropdown.select_by_visible_text(selected_option)
            print(f"Selected option: {selected_option}")
        else:
            send_telegram_message("❌ No option containing 'Student' or 'Bachelor' found!")
            return

        # Click 'Next' three times
        for i in range(3):
            next_button = driver.find_element(By.XPATH, "//input[@name='Command' and @value='Next']")
            next_button.click()
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@name='Command' and @value='Next']"))
            )

        expected_message = "For your selection there are unfortunately no appointments available"
        time.sleep(2)  # Wait for possible error message to appear

        try:
            error_message = driver.find_element(By.CSS_SELECTOR, "p.message-error")
            print(f"Error message: {error_message.text}")
            if error_message.text.strip() == expected_message:
                send_telegram_message("❌ No appointments found.")
            else:
                send_telegram_message("🎉 *Possible appointments found!*\nCheck the website immediately.")
        except Exception:
            send_telegram_message("🎉 *Possible appointments found!*\nCheck the website immediately.")

    except Exception as e:
        send_telegram_message(f"❗ Error occurred: {e}")
        print(f"An error occurred: {e}")
    finally:
        time.sleep(2)
        driver.quit()

if __name__ == "__main__":
    print(f"Script started at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    perform_actions()