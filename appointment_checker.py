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

def wait_and_verify_page_load(response, expected_element_id=None, max_retries=3):
    """
    Verify that form submission was successful and page loaded properly
    Returns (success, soup) tuple
    """
    if response.status_code != 200:
        print(f"❌ HTTP Error: {response.status_code}")
        return False, None
        
    # Parse the response
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Basic verification - check if we got HTML content
    if not soup.find('html'):
        print("❌ Response doesn't contain valid HTML")
        return False, None
        
    # If we expect a specific element, check for it
    if expected_element_id:
        target_element = soup.find(id=expected_element_id)
        if not target_element:
            print(f"❌ Expected element '{expected_element_id}' not found in response")
            print(f"📄 Page title: {soup.title.string if soup.title else 'No title'}")
            # Debug: print first 500 chars of page content
            page_text = soup.get_text()[:500]
            print(f"📄 Page content preview: {page_text}")
            return False, soup  # Return soup anyway for debugging
            
    return True, soup

def submit_form_with_verification(session, form_action, form_data, step_name, expected_element_id=None):
    """
    Submit form and verify the response with proper waiting
    """
    print(f"📤 Submitting form for {step_name}...")
    print(f"   Action: {form_action}")
    print(f"   Data: {form_data}")
    
    # Submit the form
    response = session.post(form_action, data=form_data, timeout=30)
    
    # Wait a bit for server processing (mimic your time.sleep(3))
    time.sleep(3)
    
    # Verify the response
    success, soup = wait_and_verify_page_load(response, expected_element_id)
    
    if not success:
        error_msg = f"❌ Form submission failed for {step_name}"
        print(error_msg)
        send_telegram_message(f"{error_msg}\n\nHTTP Status: {response.status_code}")
        return None, None
        
    print(f"✅ {step_name} completed successfully")
    return response, soup

def perform_appointment_check():
    """
    Enhanced version with proper waiting and verification
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
        print("📱 Enhanced version with proper waiting and verification...")
        
        # Step 1: Load initial page
        print("1️⃣ Loading main page...")
        time.sleep(3)  # Initial wait like your Selenium
        
        response1 = session.get("https://appointment.bmeia.gv.at", timeout=30)
        
        success, soup1 = wait_and_verify_page_load(response1, expected_element_id="Office")
        if not success:
            send_telegram_message("❌ Failed to load main page or Office dropdown not found")
            return
            
        print("✅ Main page loaded and Office dropdown confirmed")
        
        # Step 2: Prepare first form (Office selection)
        print("2️⃣ Preparing Office selection...")
        
        form1 = soup1.find('form')
        if not form1:
            send_telegram_message("❌ No form found on main page")
            return
            
        # Find KAIRO option
        office_select = soup1.find('select', {'id': 'Office'})
        kairo_option = None
        options = office_select.find_all('option')
        for option in options:
            if 'KAIRO' in option.text.upper():
                kairo_option = option
                break
                
        if not kairo_option:
            send_telegram_message("❌ KAIRO option not found")
            return
            
        print(f"✅ Found KAIRO option: {kairo_option.text.strip()}")
        
        # Prepare form data
        form_data1 = {}
        for input_field in form1.find_all(['input', 'select']):
            name = input_field.get('name')
            if name:
                if name == 'Office':
                    form_data1[name] = kairo_option.get('value')
                elif input_field.get('type') == 'hidden':
                    form_data1[name] = input_field.get('value', '')
                elif input_field.get('type') == 'submit':
                    form_data1[name] = input_field.get('value', 'Submit')
        
        # Get form action
        form_action1 = form1.get('action', '')
        if form_action1.startswith('/'):
            form_action1 = "https://appointment.bmeia.gv.at" + form_action1
        elif not form_action1.startswith('http'):
            form_action1 = "https://appointment.bmeia.gv.at/" + form_action1
        
        # Step 3: Submit first form with verification
        response2, soup2 = submit_form_with_verification(
            session, form_action1, form_data1, 
            "Office selection", expected_element_id="CalendarId"
        )
        
        if not response2:
            return  # Error already reported
            
        # Step 4: Process Calendar dropdown
        print("3️⃣ Processing Calendar dropdown...")
        
        calendar_select = soup2.find('select', {'id': 'CalendarId'})
        if not calendar_select:
            # This should not happen if verification worked, but let's be safe
            send_telegram_message("❌ CalendarId dropdown still not found after successful form submission")
            return
            
        # Get calendar options and check count
        calendar_options = calendar_select.find_all('option')
        current_count = len(calendar_options)
        expected_count = 9
        
        print(f"📋 Found {current_count} calendar options:")
        for i, opt in enumerate(calendar_options, 1):
            print(f"   {i}. {opt.text.strip()}")
            
        # Check if count changed
        if current_count != expected_count:
            change_message = f"""📊 OPTIONS COUNT CHANGED!

Expected: {expected_count} options
Found: {current_count} options

This could indicate appointment availability changed!"""
            print("⚠️ Options count changed - sending alert")
            send_urgent_notification(change_message)
            return
            
        # Find bachelor option
        print("4️⃣ Looking for 'bachelor' option...")
        
        selected_option = None
        for opt in calendar_options:
            opt_text = opt.text.lower()
            if "student" in opt_text or "bachelor" in opt_text:
                selected_option = opt
                print(f"✅ Found target option: {opt.text.strip()}")
                break
                
        if not selected_option:
            send_telegram_message("❌ No option containing 'Student' or 'Bachelor' found")
            return
            
        # Step 5: Prepare and submit calendar form
        form2 = soup2.find('form')
        if not form2:
            send_telegram_message("❌ No form found on calendar page")
            return
            
        form_data2 = {}
        for input_field in form2.find_all(['input', 'select']):
            name = input_field.get('name')
            if name:
                if name == 'CalendarId':
                    form_data2[name] = selected_option.get('value')
                elif input_field.get('type') == 'hidden':
                    form_data2[name] = input_field.get('value', '')
                elif input_field.get('type') == 'submit' and 'Next' in str(input_field.get('value', '')):
                    form_data2[name] = input_field.get('value', 'Next')
        
        form_action2 = form2.get('action', '')
        if form_action2.startswith('/'):
            form_action2 = "https://appointment.bmeia.gv.at" + form_action2
        elif not form_action2.startswith('http'):
            form_action2 = "https://appointment.bmeia.gv.at/" + form_action2
            
        # Submit calendar form
        response3, soup3 = submit_form_with_verification(
            session, form_action2, form_data2, 
            "Calendar selection (first Next)"
        )
        
        if not response3:
            return
            
        # Steps 6 & 7: Click Next two more times
        current_response = response3
        current_soup = soup3
        
        for click_num in [2, 3]:
            print(f"5️⃣ Clicking Next button ({click_num}/3)...")
            
            form_current = current_soup.find('form')
            if not form_current:
                print(f"⚠️ No form found for Next click {click_num}")
                break
                
            # Check if Next button exists
            next_button = form_current.find('input', {'name': 'Command', 'value': 'Next'})
            if not next_button:
                print(f"⚠️ No Next button found for click {click_num} - might have reached final page")
                break
                
            # Prepare form data
            form_data_next = {}
            for input_field in form_current.find_all(['input', 'select']):
                name = input_field.get('name')
                if name:
                    if input_field.get('type') == 'hidden':
                        form_data_next[name] = input_field.get('value', '')
                    elif input_field.get('name') == 'Command' and input_field.get('value') == 'Next':
                        form_data_next[name] = 'Next'
            
            form_action_next = form_current.get('action', '')
            if form_action_next.startswith('/'):
                form_action_next = "https://appointment.bmeia.gv.at" + form_action_next
            elif not form_action_next.startswith('http'):
                form_action_next = "https://appointment.bmeia.gv.at/" + form_action_next
                
            # Submit Next form
            current_response, current_soup = submit_form_with_verification(
                session, form_action_next, form_data_next, 
                f"Next click {click_num}"
            )
            
            if not current_response:
                return
        
        # Step 8: Check final page for appointment availability
        print("6️⃣ Checking final page for appointment availability...")
        
        if not current_soup:
            send_telegram_message("❌ No valid response from final page")
            return
            
        # Look for the specific error message
        expected_message = "For your selection there are unfortunately no appointments available"
        
        # Check for error message element
        error_message_element = current_soup.find('p', class_='message-error')
        
        if error_message_element:
            error_text = error_message_element.get_text().strip()
            print(f"📄 Found error message: {error_text}")
            
            if error_text == expected_message:
                print("📅 No appointments found (expected message)")
                current_hour = datetime.utcnow().hour
                if current_hour % 6 == 0:  # Every 6 hours
                    send_telegram_message("🔄 Status: No appointments available (checker working normally)")
            else:
                alert_msg = f"""⚠️ UNEXPECTED ERROR MESSAGE

Expected: "{expected_message}"
Found: "{error_text}"

This might indicate a change in the website or possible appointments!"""
                print("⚠️ Unexpected error message - sending alert")
                send_urgent_notification(alert_msg)
        else:
            # No error message found - possible appointments!
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
    send_telegram_message("🤖 Enhanced appointment checker starting up...")
    
    perform_appointment_check()
    
    print("✅ Check completed")