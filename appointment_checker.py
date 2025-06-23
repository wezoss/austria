import requests
from bs4 import BeautifulSoup
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

def print_snippet(text, phrase=None, window=80):
    if not phrase or phrase.lower() not in text.lower():
        return text[:window] + ("..." if len(text) > window else "")
    idx = text.lower().find(phrase.lower())
    start = max(0, idx - window//2)
    end = min(len(text), idx + len(phrase) + window//2)
    return text[start:end].replace('\n', '\\n')

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
        print(f"🚀 Appointment checker started at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print("➡️ Step 1: Load main page")
        response1 = session.get("https://appointment.bmeia.gv.at", timeout=30)
        print(f"   ...Status: {response1.status_code}")
        soup1 = BeautifulSoup(response1.content, 'html.parser')

        form1 = soup1.find('form')
        office_select = form1.find('select', {'id': 'Office'}) if form1 else None
        if not office_select:
            print("❌ Office dropdown not found")
            send_telegram_message("❌ Office dropdown not found")
            return

        kairo_option = None
        for option in office_select.find_all('option'):
            if 'KAIRO' in option.text.upper():
                kairo_option = option
                break
        if not kairo_option:
            print("❌ KAIRO option not found")
            send_telegram_message("❌ KAIRO option not found in Office dropdown")
            return

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

        print(f"➡️ Step 2: Submit Office form with Office={form_data1['Office']!r}")
        response2 = session.post(form_action1, data=form_data1, timeout=30)
        print(f"   ...Status: {response2.status_code}")
        soup2 = BeautifulSoup(response2.content, 'html.parser')

        calendar_select = soup2.find('select', {'id': 'CalendarId'})
        if not calendar_select:
            print("❌ CalendarId dropdown not found")
            send_telegram_message("❌ CalendarId dropdown not found after Office selection (even after clicking Next)")
            return
        calendar_options = calendar_select.find_all('option')
        selected_option = None
        for opt in calendar_options:
            if "bachelor" in opt.text.lower():
                selected_option = opt
                break
        if not selected_option:
            print("❌ No 'bachelor' option in CalendarId")
            send_telegram_message("❌ No 'bachelor' option in CalendarId")
            return

        chosen_cal_value = selected_option.get('value')
        if chosen_cal_value is None or chosen_cal_value == "":
            chosen_cal_value = selected_option.text.strip()

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

        print(f"➡️ Step 3: Submit CalendarId form with CalendarId={form_data2['CalendarId']!r}")
        current_response = session.post(form_action2, data=form_data2, timeout=30)
        print(f"   ...Status: {current_response.status_code}")

        # Next 2 forms: just "Next"
        for idx in range(2):
            print(f"➡️ Step {4+idx}: Submit form with only 'Next'")
            soup = BeautifulSoup(current_response.content, 'html.parser')
            form = soup.find('form')
            if not form:
                print("   ...No more forms found.")
                break
            form_data_next = {}
            for inp in form.find_all(['input', 'select']):
                name = inp.get('name')
                if not name:
                    continue
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
            print(f"   ...Status: {current_response.status_code}")

        # No further submission! Just check the result page.
        print("========= FINAL PAGE HTML START =========")
        print(current_response.text)
        print("========= END FINAL PAGE HTML =========")

        print("➡️ Step 6: Inspect final page for appointment status")
        final_soup = BeautifulSoup(current_response.content, 'html.parser')
        expected_message = "For your selection there are unfortunately no appointments available"
        page_text = final_soup.get_text(separator=" ", strip=True)
        found = False
        if expected_message.lower() in page_text.lower():
            snippet = print_snippet(page_text, expected_message)
            print(f"   ...Found expected message in page: {snippet!r}")
            found = True
            send_telegram_message("🔄 Status: No appointments available (checker working normally)")
        else:
            snippet = print_snippet(page_text)
            print(f"   ...No error message found. Page text snippet:\n{snippet}")
            send_telegram_message("🎉 POSSIBLE APPOINTMENTS FOUND! No error message detected on final page!")

        print(f"✅ Appointment check completed. No appointments: {found}")

    except Exception as e:
        send_telegram_message(f"❌ Exception: {str(e)}")
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    perform_appointment_check() 