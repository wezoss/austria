import requests
from bs4 import BeautifulSoup
import time
import os
import sys
from datetime import datetime
import json

def send_telegram_message(message, bot_token=None, chat_id=None):
    """Send message via Telegram Bot"""
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
        
        if response.status_code == 200:
            print("✅ Telegram message sent successfully")
            return True
        else:
            print(f"❌ Telegram send failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending Telegram: {e}")
        return False

def send_urgent_notification(message):
    """Send urgent notification for appointments found"""
    urgent_message = f"""🚨🚨🚨 URGENT ALERT 🚨🚨🚨

{message}

⚡ ACTION REQUIRED: Check the appointment website IMMEDIATELY!

This is an automated alert from your appointment checker."""
    
    return send_telegram_message(urgent_message)

def perform_appointment_check():
    """
    Mimics the exact Selenium process:
    1. Go to website
    2. Select KAIRO
    3. Click Next
    4. Select dropdown with "bachelor"
    5. Click Next (3 times)
    6. Check for error message
    """
    
    session = requests.Session()
    
    # Mimic browser headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    })
    
    try:
        print(f"🚀 Starting appointment check at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print("📱 Mimicking Selenium process step by step...")
        
        # Step 1: Load initial page (equivalent to driver.get())
        print("1️⃣ Loading main page...")
        time.sleep(3)  # Mimic the 3-second wait
        
        response1 = session.get("https://appointment.bmeia.gv.at", timeout=30)
        
        if response1.status_code != 200:
            error_msg = f"❌ Failed to load main page: HTTP {response1.status_code}"
            print(error_msg)
            send_telegram_message(error_msg)
            return
            
        soup1 = BeautifulSoup(response1.content, 'html.parser')
        print("✅ Main page loaded successfully")
        
        # Step 2: Find and prepare first form (Office selection)
        print("2️⃣ Looking for Office dropdown...")
        
        form1 = soup1.find('form')
        if not form1:
            error_msg = "❌ No form found on main page"
            print(error_msg)
            send_telegram_message(error_msg)
            return
            
        # Find Office dropdown
        office_select = soup1.find('select', {'id': 'Office'})
        if not office_select:
            error_msg = "❌ Office dropdown not found"
            print(error_msg)
            send_telegram_message(error_msg)
            return
            
        # Find KAIRO option
        kairo_option = None
        options = office_select.find_all('option')
        for option in options:
            if 'KAIRO' in option.text.upper():
                kairo_option = option
                break
                
        if not kairo_option:
            error_msg = "❌ KAIRO option not found in Office dropdown"
            print(error_msg)
            send_telegram_message(error_msg)
            return
            
        print(f"✅ Found KAIRO option: {kairo_option.text.strip()}")
        
        # Step 3: Prepare form data for first submission
        form_data1 = {}
        
        # Get all form fields
        for input_field in form1.find_all(['input', 'select']):
            name = input_field.get('name')
            if name:
                if name == 'Office':
                    form_data1[name] = kairo_option.get('value')
                elif input_field.get('type') == 'hidden':
                    form_data1[name] = input_field.get('value', '')
                elif input_field.get('type') == 'submit' and input_field.get('name') == 'Command':
                    form_data1[name] = input_field.get('value', 'Submit')
        
        # Get form action
        form_action1 = form1.get('action', '')
        if form_action1.startswith('/'):
            form_action1 = "https://appointment.bmeia.gv.at" + form_action1
        elif not form_action1.startswith('http'):
            form_action1 = "https://appointment.bmeia.gv.at/" + form_action1
            
        print(f"📤 Submitting first form (selecting KAIRO)...")
        print(f"   Form action: {form_action1}")
        print(f"   Form data: {form_data1}")
        
        # Step 4: Submit first form (equivalent to first submit_button.click())
        response2 = session.post(form_action1, data=form_data1, timeout=30)
        
        if response2.status_code != 200:
            error_msg = f"❌ Failed to submit first form: HTTP {response2.status_code}"
            print(error_msg)
            send_telegram_message(error_msg)
            return
            
        soup2 = BeautifulSoup(response2.content, 'html.parser')
        print("✅ First form submitted successfully")
        
        # Step 5: Find Calendar dropdown (equivalent to WebDriverWait for CalendarId)
        print("3️⃣ Looking for Calendar dropdown...")
        
        calendar_select = soup2.find('select', {'id': 'CalendarId'})
        if not calendar_select:
            error_msg = "❌ CalendarId dropdown not found"
            print(error_msg)
            send_telegram_message(error_msg)
            return
            
        # Get calendar options and check count (equivalent to your options counting)
        calendar_options = calendar_select.find_all('option')
        current_count = len(calendar_options)
        expected_count = 9
        
        print(f"📋 Found {current_count} calendar options:")
        for i, opt in enumerate(calendar_options, 1):
            print(f"   {i}. {opt.text.strip()}")
            
        # Check if count changed (equivalent to your count comparison)
        if current_count != expected_count:
            change_message = f"""📊 OPTIONS COUNT CHANGED!

Expected: {expected_count} options
Found: {current_count} options

This could indicate appointment availability changed!"""
            print("⚠️ Options count changed - sending alert")
            send_urgent_notification(change_message)
            return
            
        # Step 6: Find option containing "bachelor" (equivalent to your bachelor/student search)
        print("4️⃣ Looking for 'bachelor' option...")
        
        selected_option = None
        for opt in calendar_options:
            opt_text = opt.text.lower()
            if "student" in opt_text or "bachelor" in opt_text:
                selected_option = opt
                print(f"✅ Found target option: {opt.text.strip()}")
                break
                
        if not selected_option:
            error_msg = "❌ No option containing 'Student' or 'Bachelor' found"
            print(error_msg)
            send_telegram_message(error_msg)
            return
            
        # Step 7: Prepare second form (Calendar selection)
        form2 = soup2.find('form')
        if not form2:
            error_msg = "❌ No form found on second page"
            print(error_msg)
            send_telegram_message(error_msg)
            return
            
        form_data2 = {}
        for input_field in form2.find_all(['input', 'select']):
            name = input_field.get('name')
            if name:
                if name == 'CalendarId':
                    form_data2[name] = selected_option.get('value')
                elif input_field.get('type') == 'hidden':
                    form_data2[name] = input_field.get('value', '')
                elif input_field.get('type') == 'submit' and 'Next' in input_field.get('value', ''):
                    form_data2[name] = input_field.get('value', 'Next')
        
        form_action2 = form2.get('action', '')
        if form_action2.startswith('/'):
            form_action2 = "https://appointment.bmeia.gv.at" + form_action2
        elif not form_action2.startswith('http'):
            form_action2 = "https://appointment.bmeia.gv.at/" + form_action2
            
        print(f"📤 Submitting second form (selecting bachelor option)...")
        
        # Step 8: Submit second form (first Next click)
        response3 = session.post(form_action2, data=form_data2, timeout=30)
        
        if response3.status_code != 200:
            error_msg = f"❌ Failed to submit second form: HTTP {response3.status_code}"
            print(error_msg)
            send_telegram_message(error_msg)
            return
            
        print("✅ Second form submitted (first Next)")
        
        # Step 9 & 10: Click Next two more times (equivalent to your 3 Next clicks)
        current_response = response3
        
        for click_num in [2, 3]:
            print(f"5️⃣ Clicking Next button ({click_num}/3)...")
            
            soup_current = BeautifulSoup(current_response.content, 'html.parser')
            form_current = soup_current.find('form')
            
            if not form_current:
                print(f"⚠️ No form found for Next click {click_num}")
                break
                
            # Find Next button
            next_button = form_current.find('input', {'name': 'Command', 'value': 'Next'})
            if not next_button:
                print(f"⚠️ No Next button found for click {click_num}")
                break
                
            # Prepare form data for Next click
            form_data_next = {}
            for input_field in form_current.find_all(['input', 'select']):
                name = input_field.get('name')
                if name:
                    if input_field.get('type') == 'hidden':
                        form_data_next[name] = input_field.get('value', '')
                    elif input_field.get('type') == 'submit' and input_field.get('value') == 'Next':
                        form_data_next[name] = 'Next'
                    elif input_field.name == 'select':
                        # Keep any selected values from previous steps
                        form_data_next[name] = input_field.get('value', '')
            
            form_action_next = form_current.get('action', '')
            if form_action_next.startswith('/'):
                form_action_next = "https://appointment.bmeia.gv.at" + form_action_next
            elif not form_action_next.startswith('http'):
                form_action_next = "https://appointment.bmeia.gv.at/" + form_action_next
                
            # Submit Next form
            current_response = session.post(form_action_next, data=form_data_next, timeout=30)
            
            if current_response.status_code != 200:
                error_msg = f"❌ Failed Next click {click_num}: HTTP {current_response.status_code}"
                print(error_msg)
                send_telegram_message(error_msg)
                return
                
            print(f"✅ Next click {click_num} completed")
        
        # Step 11: Check final page for appointment availability message
        print("6️⃣ Checking final page for appointment availability...")
        
        final_soup = BeautifulSoup(current_response.content, 'html.parser')
        
        # Look for the specific error message (equivalent to your expected_message check)
        expected_message = "For your selection there are unfortunately no appointments available"
        
        # Check for error message element
        error_message_element = final_soup.find('p', class_='message-error')
        
        if error_message_element:
            error_text = error_message_element.get_text().strip()
            print(f"📄 Found error message: {error_text}")
            
            if error_text == expected_message:
                print("📅 No appointments found (expected message)")
                # Send status update every few hours to confirm it's working
                current_hour = datetime.utcnow().hour
                if current_hour % 6 == 0:  # Every 6 hours
                    send_telegram_message("🔄 Status: No appointments available (checker working normally)")
            else:
                # Different error message - possible change
                alert_msg = f"""⚠️ UNEXPECTED ERROR MESSAGE

Expected: "{expected_message}"
Found: "{error_text}"

This might indicate a change in the website or possible appointments!"""
                print("⚠️ Unexpected error message - sending alert")
                send_urgent_notification(alert_msg)
        else:
            # No error message found - possible appointments! (equivalent to your except block)
            success_msg = """🎉🎉🎉 POSSIBLE APPOINTMENTS FOUND! 🎉🎉🎉

No error message detected on final page!
This usually means appointments are available!"""
            print("🎉 No error message found - appointments might be available!")
            send_urgent_notification(success_msg)
            
        print("✅ Appointment check completed successfully")
        
    except requests.exceptions.Timeout:
        error_msg = "⏰ Request timeout - website may be slow"
        print(error_msg)
        send_telegram_message(error_msg)
    except requests.exceptions.ConnectionError:
        error_msg = "🌐 Connection error - check internet or website status"
        print(error_msg)
        send_telegram_message(error_msg)
    except Exception as e:
        error_msg = f"❌ Unexpected error: {str(e)}"
        print(error_msg)
        send_telegram_message(error_msg)

if __name__ == "__main__":
    print(f"🚀 Appointment checker started at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    # Send startup notification
    send_telegram_message("🤖 Appointment checker starting up...")
    
    perform_appointment_check()
    
    print("✅ Check completed")