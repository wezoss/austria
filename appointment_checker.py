import requests
from bs4 import BeautifulSoup
import time
import os
from datetime import datetime

def send_telegram_message(message, bot_token=None, chat_id=None):
    try:
        bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        if not bot_token or not chat_id:
            print("❌ Telegram credentials not configured")
            return False
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        formatted_message = f"""🤖 *Appointment Checker*

{message}

📅 Time: `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`
🔗 [Check Website](https://appointment.bmeia.gv.at)"""
        payload = {
            "chat_id": chat_id,
            "text": formatted_message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error sending Telegram: {e}")
        return False

def perform_appointment_check():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
        "Origin": "https://appointment.bmeia.gv.at",
        "Referer": "https://appointment.bmeia.gv.at/"
    })

    try:
        # 1️⃣ Load main page
        response1 = session.get("https://appointment.bmeia.gv.at", timeout=30)
        if response1.status_code != 200:
            send_telegram_message(f"❌ Failed to load main page: HTTP {response1.status_code}")
            return
        soup1 = BeautifulSoup(response1.content, 'html.parser')

        # 2️⃣ Prepare Office form and submit with "Next"
        form1 = soup1.find('form')
        office_select = form1.find('select', {'id': 'Office'}) if form1 else None
        if not office_select:
            send_telegram_message("❌ Office dropdown not found")
            return

        kairo_option = None
        for option in office_select.find_all('option'):
            if 'KAIRO' in option.text.upper():
                kairo_option = option
                break
        if not kairo_option:
            send_telegram_message("❌ KAIRO option not found in Office dropdown")
            return

        # Use the value if present, else use the text.
        chosen_value = kairo_option.get('value')
        if chosen_value is None or chosen_value == "":
            chosen_value = kairo_option.text.strip()

        form_data1 = {}
        for inp in form1.find_all(['input', 'select']):
            name = inp.get('name')
            if not name:
                continue
            if inp.name == 'select' and name == 'Office':
                form_data1[name] = chosen_value
            elif inp.get('type') == 'hidden':
                form_data1[name] = inp.get('value', '')
            elif inp.get('type') == 'submit' and inp.get('value') == 'Next':
                form_data1[name] = inp.get('value')

        form_action1 = form1.get('action', '')
        if form_action1.startswith('/'):
            form_action1 = "https://appointment.bmeia.gv.at" + form_action1
        elif not form_action1.startswith('http'):
            form_action1 = "https://appointment.bmeia.gv.at/" + form_action1

        # 3️⃣ Submit Office form with "Next"
        time.sleep(2)
        response2 = session.post(form_action1, data=form_data1, timeout=30)
        if response2.status_code != 200:
            send_telegram_message(f"❌ Failed to submit Office selection: HTTP {response2.status_code}")
            return
        soup2 = BeautifulSoup(response2.content, 'html.parser')

        # 4️⃣ Find CalendarId dropdown and select "bachelor" option
        calendar_select = soup2.find('select', {'id': 'CalendarId'})
        if not calendar_select:
            send_telegram_message("❌ CalendarId dropdown not found after Office selection (even after clicking Next)")
            return
        calendar_options = calendar_select.find_all('option')
        selected_option = None
        for opt in calendar_options:
            if "bachelor" in opt.text.lower():
                selected_option = opt
                break
        if not selected_option:
            send_telegram_message("❌ No 'bachelor' option in CalendarId")
            return

        chosen_cal_value = selected_option.get('value')
        if chosen_cal_value is None or chosen_cal_value == "":
            chosen_cal_value = selected_option.text.strip()

        # Prepare calendar form
        form2 = soup2.find('form')
        form_data2 = {}
        for inp in form2.find_all(['input', 'select']):
            name = inp.get('name')
            if not name:
                continue
            if inp.name == 'select' and name == 'CalendarId':
                form_data2[name] = chosen_cal_value
            elif inp.get('type') == 'hidden':
                form_data2[name] = inp.get('value', '')
            elif inp.get('type') == 'submit' and inp.get('value') == 'Next':
                form_data2[name] = inp.get('value')

        form_action2 = form2.get('action', '')
        if form_action2.startswith('/'):
            form_action2 = "https://appointment.bmeia.gv.at" + form_action2
        elif not form_action2.startswith('http'):
            form_action2 = "https://appointment.bmeia.gv.at/" + form_action2

        # 5️⃣ Submit CalendarId form with "Next"
        current_response = session.post(form_action2, data=form_data2, timeout=30)

        # 6️⃣ Submit next form with "Next" only (no extra input)
        for _ in range(2):
            soup = BeautifulSoup(current_response.content, 'html.parser')
            form = soup.find('form')
            if not form:
                break
            form_data_next = {}
            for inp in form.find_all(['input', 'select']):
                name = inp.get('name')
                if not name:
                    continue
                # Only send hidden fields and the submit "Next"
                if inp.get('type') == 'hidden':
                    form_data_next[name] = inp.get('value', '')
                elif inp.get('type') == 'submit' and inp.get('value') == 'Next':
                    form_data_next[name] = inp.get('value')
            form_action_next = form.get('action', '')
            if form_action_next.startswith('/'):
                form_action_next = "https://appointment.bmeia.gv.at" + form_action_next
            elif not form_action_next.startswith('http'):
                form_action_next = "https://appointment.bmeia.gv.at/" + form_action_next
            current_response = session.post(form_action_next, data=form_data_next, timeout=30)

        # 7️⃣ Check for expected message or appointments
        final_soup = BeautifulSoup(current_response.content, 'html.parser')
        expected_message = "For your selection there are unfortunately no appointments available"
        error_message_element = final_soup.find('p', class_='message-error')
        if error_message_element:
            error_text = error_message_element.get_text().strip()
            if expected_message in error_text:
                send_telegram_message("🔄 Status: No appointments available (checker working normally)")
            else:
                send_telegram_message(f"⚠️ Unexpected error message:\n\n{error_text}")
        else:
            # If the message is not there, appointments may be possible!
            send_telegram_message("🎉 POSSIBLE APPOINTMENTS FOUND! No error message detected on final page!")

        print("✅ Appointment check completed successfully")

    except Exception as e:
        send_telegram_message(f"❌ Exception: {str(e)}")
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    print(f"🚀 Appointment checker started at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    perform_appointment_check()