import requests
from bs4 import BeautifulSoup
import time
import os
import sys
from datetime import datetime
import json

def send_telegram_message(message, bot_token=None, chat_id=None):
    """Send message via Telegram Bot with enhanced formatting"""
    try:
        # Use environment variables if not provided
        bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            print("❌ Telegram credentials not configured")
            return False
            
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        # Enhanced message formatting
        formatted_message = f"""🤖 *Appointment Checker Alert*

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
            print(f"❌ Telegram send failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending Telegram message: {e}")
        return False

def send_urgent_notification(message):
    """Send urgent notification with special formatting"""
    urgent_message = f"""🚨🚨🚨 URGENT ALERT 🚨🚨🚨

{message}

⚡ ACTION REQUIRED: Check the appointment website IMMEDIATELY!

This is an automated alert from your appointment checker."""
    
    return send_telegram_message(urgent_message)

def check_appointments():
    """Check appointments using requests instead of Selenium"""
    session = requests.Session()
    
    # Add headers to mimic a real browser
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    try:
        print(f"🔄 Starting appointment check at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        # Send startup notification (optional, comment out if too many messages)
        # send_telegram_message("🔄 Appointment checker started...")
        
        # First request to get the main page
        response = session.get("https://appointment.bmeia.gv.at", timeout=30)
        
        if response.status_code != 200:
            error_msg = f"❌ Failed to load main page: HTTP {response.status_code}"
            print(error_msg)
            send_telegram_message(error_msg)
            return
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the form and required fields
        form = soup.find('form')
        if not form:
            error_msg = "❌ No form found on the page - website structure may have changed"
            print(error_msg)
            send_telegram_message(error_msg)
            return
            
        # Get form action
        form_action = form.get('action', '')
        if form_action.startswith('/'):
            form_action = "https://appointment.bmeia.gv.at" + form_action
        elif not form_action.startswith('http'):
            form_action = "https://appointment.bmeia.gv.at/" + form_action
            
        # Prepare form data for first submission (select KAIRO)
        form_data = {}
        
        # Find all input fields and their values
        for input_field in form.find_all(['input', 'select']):
            name = input_field.get('name')
            if name:
                if input_field.name == 'select' and name == 'Office':
                    # Select KAIRO option
                    options = input_field.find_all('option')
                    kairo_found = False
                    for option in options:
                        if 'KAIRO' in option.text.upper():
                            form_data[name] = option.get('value')
                            kairo_found = True
                            break
                    if not kairo_found:
                        error_msg = "❌ KAIRO option not found in office selection"
                        print(error_msg)
                        send_telegram_message(error_msg)
                        return
                elif input_field.get('type') == 'hidden':
                    form_data[name] = input_field.get('value', '')
                elif input_field.get('type') == 'submit' and input_field.get('name') == 'Command':
                    form_data[name] = input_field.get('value', 'Submit')
        
        print(f"📤 Submitting form to: {form_action}")
        print(f"📝 Form data: {form_data}")
        
        # Submit the first form
        response2 = session.post(form_action, data=form_data, timeout=30)
        
        if response2.status_code != 200:
            error_msg = f"❌ Failed to submit first form: HTTP {response2.status_code}"
            print(error_msg)
            send_telegram_message(error_msg)
            return
            
        # Parse the second page
        soup2 = BeautifulSoup(response2.content, 'html.parser')
        
        # Look for calendar dropdown
        calendar_select = soup2.find('select', {'id': 'CalendarId'})
        if calendar_select:
            options = calendar_select.find_all('option')
            current_count = len(options)
            expected_count = 9
            
            print(f"📋 Found {current_count} calendar options:")
            for i, opt in enumerate(options, 1):
                print(f"   {i}. {opt.text.strip()}")
                
            # Check if count changed (possible new appointments)
            if current_count != expected_count:
                message = f"""📊 APPOINTMENT OPTIONS CHANGED!

Expected: {expected_count} options
Found: {current_count} options

This could indicate new appointments are available!"""
                print(message)
                send_urgent_notification(message)
                return
            
            # Look for student/bachelor options
            selected_option = None
            for opt in options:
                opt_text = opt.text.lower()
                if "student" in opt_text or "bachelor" in opt_text:
                    selected_option = opt
                    break
                    
            if not selected_option:
                message = "❌ Student/Bachelor appointment type not available in current options"
                print(message)
                send_telegram_message(message)
                return
            else:
                print(f"✅ Found target option: {selected_option.text.strip()}")
        
        # Look for the "no appointments" message
        error_messages = soup2.find_all('p', class_='message-error')
        no_appointments_messages = soup2.find_all(text=lambda text: text and "no appointments available" in text.lower())
        
        no_appointments_found = len(error_messages) > 0 or len(no_appointments_messages) > 0
        
        if not no_appointments_found:
            # Possible appointments found!
            message = """🎉🎉🎉 APPOINTMENTS MIGHT BE AVAILABLE! 🎉🎉🎉

No 'no appointments available' message detected!
Check the website IMMEDIATELY:"""
            print(message)
            send_urgent_notification(message)
        else:
            print("📅 No appointments currently available (normal status)")
            # Uncomment next line if you want confirmation messages every 5 minutes
            # send_telegram_message("📅 Check complete: No appointments available")
            
    except requests.exceptions.Timeout:
        error_msg = "⏰ Request timeout - website may be slow or down"
        print(error_msg)
        send_telegram_message(error_msg)
    except requests.exceptions.ConnectionError:
        error_msg = "🌐 Connection error - check internet or website status"
        print(error_msg)
        send_telegram_message(error_msg)
    except Exception as e:
        error_msg = f"❌ Unexpected error occurred: {str(e)}"
        print(error_msg)
        send_telegram_message(error_msg)

if __name__ == "__main__":
    print(f"🚀 Appointment checker started at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    # Test Telegram connection first
    if send_telegram_message("🤖 Appointment checker is starting up..."):
        print("✅ Telegram connection successful")
    else:
        print("❌ Telegram connection failed - check your secrets")
    
    check_appointments()
    print("✅ Check completed")