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
        
        formatted_message = f"""🤖 *Debug Mode*

{message}

📅 Time: `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`"""

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

def debug_page_content(soup, step_name):
    """Debug function to show what's actually on the page"""
    print(f"\n🔍 DEBUGGING {step_name.upper()}:")
    
    # Show page title
    title = soup.title.string if soup.title else "No title"
    print(f"📄 Page title: {title}")
    
    # Show all form elements
    forms = soup.find_all('form')
    print(f"📋 Found {len(forms)} form(s)")
    
    for i, form in enumerate(forms, 1):
        print(f"   Form {i}:")
        print(f"   - Action: {form.get('action', 'No action')}")
        
        # Show all inputs and selects
        inputs = form.find_all(['input', 'select'])
        print(f"   - Found {len(inputs)} input/select elements:")
        
        for inp in inputs:
            name = inp.get('name', 'No name')
            input_type = inp.get('type', inp.name)
            input_id = inp.get('id', 'No ID')
            
            if inp.name == 'select':
                options = inp.find_all('option')
                print(f"     • SELECT: name='{name}', id='{input_id}', {len(options)} options")
                for opt in options[:3]:  # Show first 3 options
                    print(f"       - {opt.text.strip()}")
                if len(options) > 3:
                    print(f"       - ... and {len(options)-3} more")
            else:
                value = inp.get('value', 'No value')
                print(f"     • INPUT: name='{name}', type='{input_type}', id='{input_id}', value='{value}'")
    
    # Show any error messages
    error_msgs = soup.find_all('p', class_='message-error')
    if error_msgs:
        print(f"❌ Found {len(error_msgs)} error message(s):")
        for msg in error_msgs:
            print(f"   - {msg.get_text().strip()}")
    
    # Show first 300 chars of page text
    page_text = soup.get_text()
    clean_text = ' '.join(page_text.split())[:300]
    print(f"📝 Page text preview: {clean_text}...")
    print("-" * 60)

def perform_debug_check():
    """Debug version to see exactly what's happening"""
    
    session = requests.Session()
    
    # Browser headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    try:
        print(f"🚀 DEBUG MODE: Starting at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        # Step 1: Load main page
        print("1️⃣ Loading main page...")
        response1 = session.get("https://appointment.bmeia.gv.at", timeout=30)
        
        print(f"📊 Main page response: HTTP {response1.status_code}")
        print(f"📊 Content length: {len(response1.content)} bytes")
        print(f"📊 Content type: {response1.headers.get('content-type', 'Unknown')}")
        
        if response1.status_code != 200:
            send_telegram_message(f"❌ Main page failed: HTTP {response1.status_code}")
            return
            
        soup1 = BeautifulSoup(response1.content, 'html.parser')
        debug_page_content(soup1, "MAIN PAGE")
        
        # Check if Office dropdown exists
        office_select = soup1.find('select', {'id': 'Office'})
        if not office_select:
            send_telegram_message("❌ DEBUG: Office dropdown not found on main page!")
            return
            
        print("✅ Office dropdown found!")
        
        # Find KAIRO option
        kairo_option = None
        options = office_select.find_all('option')
        print(f"📋 Office dropdown has {len(options)} options:")
        
        for i, option in enumerate(options):
            option_text = option.text.strip()
            option_value = option.get('value', 'No value')
            print(f"   {i+1}. '{option_text}' (value: '{option_value}')")
            
            if 'KAIRO' in option_text.upper():
                kairo_option = option
                print(f"   ✅ KAIRO found at position {i+1}")
                
        if not kairo_option:
            send_telegram_message("❌ DEBUG: KAIRO option not found!")
            return
            
        # Step 2: Prepare form submission
        print("\n2️⃣ Preparing form submission...")
        
        form1 = soup1.find('form')
        if not form1:
            send_telegram_message("❌ DEBUG: No form found on main page!")
            return
            
        print(f"📋 Form action: {form1.get('action', 'No action')}")
        print(f"📋 Form method: {form1.get('method', 'No method')}")
        
        # Collect ALL form data
        form_data1 = {}
        all_inputs = form1.find_all(['input', 'select'])
        
        print(f"📋 Processing {len(all_inputs)} form elements:")
        
        for inp in all_inputs:
            name = inp.get('name')
            if name:
                if name == 'Office':
                    form_data1[name] = kairo_option.get('value')
                    print(f"   ✅ Office = '{kairo_option.get('value')}' (KAIRO)")
                elif inp.get('type') == 'hidden':
                    value = inp.get('value', '')
                    form_data1[name] = value
                    print(f"   🔒 Hidden: {name} = '{value}'")
                elif inp.get('type') == 'submit':
                    value = inp.get('value', 'Submit')
                    form_data1[name] = value
                    print(f"   🔘 Submit: {name} = '{value}'")
                elif inp.name == 'select' and name != 'Office':
                    # Handle other select elements
                    value = inp.get('value', '')
                    form_data1[name] = value
                    print(f"   📋 Select: {name} = '{value}'")
        
        print(f"\n📤 Final form data: {form_data1}")
        
        # Get form action URL
        form_action1 = form1.get('action', '')
        if form_action1.startswith('/'):
            form_action1 = "https://appointment.bmeia.gv.at" + form_action1
        elif not form_action1.startswith('http'):
            form_action1 = "https://appointment.bmeia.gv.at/" + form_action1
            
        print(f"📤 Submitting to: {form_action1}")
        
        # Step 3: Submit form
        print("\n3️⃣ Submitting first form...")
        time.sleep(2)  # Wait before submission
        
        response2 = session.post(form_action1, data=form_data1, timeout=30)
        
        print(f"📊 Form submission response: HTTP {response2.status_code}")
        print(f"📊 Response length: {len(response2.content)} bytes")
        print(f"📊 Response URL: {response2.url}")
        
        if response2.status_code != 200:
            send_telegram_message(f"❌ DEBUG: Form submission failed: HTTP {response2.status_code}")
            return
            
        # Wait for page to load
        time.sleep(3)
        
        soup2 = BeautifulSoup(response2.content, 'html.parser')
        debug_page_content(soup2, "AFTER FORM SUBMISSION")
        
        # Check for CalendarId
        calendar_select = soup2.find('select', {'id': 'CalendarId'})
        
        if calendar_select:
            print("🎉 SUCCESS: CalendarId dropdown found!")
            options = calendar_select.find_all('option')
            print(f"📋 Calendar has {len(options)} options:")
            for i, opt in enumerate(options):
                print(f"   {i+1}. {opt.text.strip()}")
        else:
            print("❌ CalendarId dropdown still not found")
            
            # Check what elements DO exist with 'id' attributes
            elements_with_id = soup2.find_all(attrs={'id': True})
            print(f"📋 Found {len(elements_with_id)} elements with ID attributes:")
            for elem in elements_with_id[:10]:  # Show first 10
                print(f"   - {elem.name}: id='{elem.get('id')}'")
                
            # Send debug info to Telegram
            debug_message = f"""🔍 DEBUG: CalendarId not found

Form submission got HTTP 200 but CalendarId missing.

Found {len(elements_with_id)} elements with IDs.
Page title: {soup2.title.string if soup2.title else 'None'}

This suggests the form didn't navigate to the expected page."""
            
            send_telegram_message(debug_message)
        
        print("✅ Debug check completed")
        
    except Exception as e:
        error_msg = f"❌ Debug error: {str(e)}"
        print(error_msg)
        send_telegram_message(error_msg)

if __name__ == "__main__":
    send_telegram_message("🔍 Starting DEBUG mode to investigate form submission issue...")
    perform_debug_check()