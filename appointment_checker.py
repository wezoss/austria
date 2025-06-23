import requests
from bs4 import BeautifulSoup
import time
import os
import sys
from datetime import datetime

def send_telegram_message(message, bot_token=None, chat_id=None):
    """Send message via Telegram Bot"""
    try:
        bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            print("❌ Telegram credentials not configured")
            return False
            
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        # Split long messages
        if len(message) > 4000:
            message = message[:4000] + "... (truncated)"
        
        formatted_message = f"""🤖 *Enhanced Debug*

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

def perform_enhanced_debug():
    """Enhanced debug to see exact form submission details"""
    
    session = requests.Session()
    
    # Browser headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'no-cache'
    })
    
    try:
        print(f"🚀 ENHANCED DEBUG: Starting at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        # Step 1: Load main page
        print("=" * 60)
        print("STEP 1: LOADING MAIN PAGE")
        print("=" * 60)
        
        response1 = session.get("https://appointment.bmeia.gv.at", timeout=30)
        
        print(f"Response Status: {response1.status_code}")
        print(f"Response URL: {response1.url}")
        print(f"Content Length: {len(response1.content)}")
        
        if response1.status_code != 200:
            send_telegram_message(f"❌ Main page failed: HTTP {response1.status_code}")
            return
            
        soup1 = BeautifulSoup(response1.content, 'html.parser')
        
        # Show page title
        title = soup1.title.string if soup1.title else "No title"
        print(f"Page Title: {title}")
        
        # Find and analyze the form
        print("\n" + "-" * 40)
        print("ANALYZING MAIN PAGE FORM")
        print("-" * 40)
        
        forms = soup1.find_all('form')
        print(f"Found {len(forms)} form(s)")
        
        if not forms:
            send_telegram_message("❌ No forms found on main page!")
            return
            
        form1 = forms[0]  # Use first form
        print(f"Form action: '{form1.get('action', 'No action')}'")
        print(f"Form method: '{form1.get('method', 'No method')}'")
        
        # Show ALL form elements in detail
        print(f"\nALL FORM ELEMENTS:")
        all_elements = form1.find_all(['input', 'select', 'textarea', 'button'])
        
        for i, elem in enumerate(all_elements, 1):
            print(f"\n{i}. {elem.name.upper()}:")
            print(f"   name: '{elem.get('name', 'No name')}'")
            print(f"   id: '{elem.get('id', 'No ID')}'")
            print(f"   type: '{elem.get('type', 'No type')}'")
            print(f"   value: '{elem.get('value', 'No value')}'")
            
            if elem.name == 'select':
                options = elem.find_all('option')
                print(f"   options ({len(options)}):")
                for j, opt in enumerate(options):
                    opt_value = opt.get('value', 'No value')
                    opt_text = opt.text.strip()
                    selected = "SELECTED" if opt.get('selected') else ""
                    print(f"     {j+1}. value='{opt_value}' text='{opt_text}' {selected}")
        
        # Find Office dropdown specifically
        print(f"\n" + "-" * 40)
        print("OFFICE DROPDOWN ANALYSIS")
        print("-" * 40)
        
        office_select = soup1.find('select', {'id': 'Office'}) or soup1.find('select', {'name': 'Office'})
        
        if not office_select:
            print("❌ Office dropdown not found by ID or name!")
            # Try to find any select with office-related options
            all_selects = soup1.find_all('select')
            print(f"Found {len(all_selects)} select elements total:")
            for sel in all_selects:
                print(f"  - name: '{sel.get('name')}', id: '{sel.get('id')}'")
            send_telegram_message("❌ Office dropdown not found!")
            return
        
        print("✅ Office dropdown found!")
        print(f"Office dropdown name: '{office_select.get('name')}'")
        print(f"Office dropdown id: '{office_select.get('id')}'")
        
        # Analyze KAIRO option
        options = office_select.find_all('option')
        print(f"\nOffice options ({len(options)}):")
        
        kairo_option = None
        for i, option in enumerate(options):
            opt_value = option.get('value', 'No value')
            opt_text = option.text.strip()
            is_kairo = 'KAIRO' in opt_text.upper()
            print(f"  {i+1}. value='{opt_value}' text='{opt_text}' {'← KAIRO!' if is_kairo else ''}")
            
            if is_kairo:
                kairo_option = option
        
        if not kairo_option:
            send_telegram_message("❌ KAIRO option not found in Office dropdown!")
            return
            
        print(f"\n✅ KAIRO found: value='{kairo_option.get('value')}', text='{kairo_option.text.strip()}'")
        
        # Step 2: Prepare form submission
        print(f"\n" + "=" * 60)
        print("STEP 2: PREPARING FORM SUBMISSION")
        print("=" * 60)
        
        form_data = {}
        
        # Process each form element
        for elem in form1.find_all(['input', 'select']):
            name = elem.get('name')
            if not name:
                continue
                
            if name == 'Office' or (elem.get('id') == 'Office'):
                form_data[name] = kairo_option.get('value')
                print(f"✅ {name} = '{kairo_option.get('value')}' (KAIRO selected)")
                
            elif elem.get('type') == 'hidden':
                value = elem.get('value', '')
                form_data[name] = value
                print(f"🔒 {name} = '{value}' (hidden field)")
                
            elif elem.get('type') == 'submit':
                value = elem.get('value', 'Submit')
                form_data[name] = value
                print(f"🔘 {name} = '{value}' (submit button)")
                
            elif elem.name == 'select':
                # For other selects, use their default/selected value
                selected_opt = elem.find('option', selected=True)
                if selected_opt:
                    value = selected_opt.get('value', '')
                else:
                    # Use first option if none selected
                    first_opt = elem.find('option')
                    value = first_opt.get('value', '') if first_opt else ''
                form_data[name] = value
                print(f"📋 {name} = '{value}' (select default)")
                
            elif elem.get('type') in ['text', 'email', 'tel']:
                value = elem.get('value', '')
                form_data[name] = value
                print(f"📝 {name} = '{value}' (text input)")
        
        print(f"\nFINAL FORM DATA:")
        for key, value in form_data.items():
            print(f"  '{key}': '{value}'")
        
        # Get form action
        form_action = form1.get('action', '')
        if not form_action:
            form_action = response1.url  # Use current URL if no action
        elif form_action.startswith('/'):
            form_action = "https://appointment.bmeia.gv.at" + form_action
        elif not form_action.startswith('http'):
            form_action = "https://appointment.bmeia.gv.at/" + form_action
            
        print(f"\nForm will be submitted to: {form_action}")
        
        # Step 3: Submit the form
        print(f"\n" + "=" * 60)
        print("STEP 3: SUBMITTING FORM")
        print("=" * 60)
        
        print("Waiting 2 seconds before submission...")
        time.sleep(2)
        
        response2 = session.post(form_action, data=form_data, timeout=30)
        
        print(f"Submission Response Status: {response2.status_code}")
        print(f"Submission Response URL: {response2.url}")
        print(f"Response Content Length: {len(response2.content)}")
        
        # Check response headers
        print(f"\nResponse Headers:")
        for header, value in response2.headers.items():
            if header.lower() in ['location', 'content-type', 'set-cookie']:
                print(f"  {header}: {value}")
        
        if response2.status_code != 200:
            send_telegram_message(f"❌ Form submission failed: HTTP {response2.status_code}")
            return
        
        # Wait for page processing
        print("Waiting 3 seconds for page to load...")
        time.sleep(3)
        
        # Step 4: Analyze the response page
        print(f"\n" + "=" * 60)
        print("STEP 4: ANALYZING RESPONSE PAGE")
        print("=" * 60)
        
        soup2 = BeautifulSoup(response2.content, 'html.parser')
        
        # Page title
        title2 = soup2.title.string if soup2.title else "No title"
        print(f"Response Page Title: {title2}")
        
        # Look for CalendarId
        calendar_select = soup2.find('select', {'id': 'CalendarId'})
        print(f"CalendarId found: {'YES' if calendar_select else 'NO'}")
        
        # Show all elements with IDs
        elements_with_id = soup2.find_all(attrs={'id': True})
        print(f"\nElements with IDs ({len(elements_with_id)}):")
        for elem in elements_with_id:
            print(f"  {elem.name}: id='{elem.get('id')}'")
        
        # Show all forms on response page
        response_forms = soup2.find_all('form')
        print(f"\nForms on response page: {len(response_forms)}")
        for i, form in enumerate(response_forms, 1):
            print(f"  Form {i}: action='{form.get('action')}', method='{form.get('method')}'")
        
        # Look for any error messages
        error_elements = soup2.find_all(['p', 'div', 'span'], class_=lambda x: x and 'error' in x.lower())
        if error_elements:
            print(f"\nPossible error messages ({len(error_elements)}):")
            for elem in error_elements:
                print(f"  - {elem.get_text().strip()}")
        
        # Show first 500 chars of page text
        page_text = soup2.get_text()
        clean_text = ' '.join(page_text.split())[:500]
        print(f"\nPage text preview:\n{clean_text}...")
        
        # Send summary to Telegram
        if calendar_select:
            summary = "🎉 SUCCESS: Found CalendarId dropdown!"
        else:
            summary = f"""❌ ISSUE: CalendarId not found

Response page title: {title2}
Elements with IDs: {len(elements_with_id)}
Forms found: {len(response_forms)}

Possible causes:
1. Form validation failed
2. Missing required fields  
3. Need to handle redirects
4. Website changed structure"""
        
        send_telegram_message(summary)
        
        print("✅ Enhanced debug completed")
        
    except Exception as e:
        error_msg = f"❌ Enhanced debug error: {str(e)}"
        print(error_msg)
        send_telegram_message(error_msg)

if __name__ == "__main__":
    perform_enhanced_debug()