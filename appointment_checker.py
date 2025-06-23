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
        
        # Split very long messages
        if len(message) > 4000:
            message = message[:4000] + "\n\n...(truncated for Telegram)"
        
        formatted_message = f"""🤖 *Full Debug Analysis*

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

def perform_full_debug():
    """Complete debugging with all details printed to GitHub Actions logs"""
    
    session = requests.Session()
    
    # Browser headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'no-cache'
    })
    
    try:
        print("🚀" * 20)
        print("FULL DEBUG MODE - COMPLETE ANALYSIS")
        print("🚀" * 20)
        print(f"Start Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        # Step 1: Load main page with detailed analysis
        print("\n" + "="*80)
        print("STEP 1: LOADING AND ANALYZING MAIN PAGE")
        print("="*80)
        
        response1 = session.get("https://appointment.bmeia.gv.at", timeout=30)
        
        print(f"✅ Response Status: {response1.status_code}")
        print(f"✅ Response URL: {response1.url}")
        print(f"✅ Content Type: {response1.headers.get('content-type', 'Unknown')}")
        print(f"✅ Content Length: {len(response1.content)} bytes")
        print(f"✅ Response Headers Count: {len(response1.headers)}")
        
        # Show important headers
        print("\n📋 Important Response Headers:")
        for header in ['content-type', 'server', 'set-cookie', 'location']:
            if header in response1.headers:
                value = response1.headers[header]
                print(f"   {header}: {value}")
        
        if response1.status_code != 200:
            error_msg = f"❌ Main page request failed: HTTP {response1.status_code}"
            print(error_msg)
            send_telegram_message(error_msg)
            return
            
        # Parse the HTML
        soup1 = BeautifulSoup(response1.content, 'html.parser')
        
        # Show page basics
        title = soup1.title.string.strip() if soup1.title else "No title"
        print(f"\n📄 Page Title: '{title}'")
        
        # Count elements
        all_elements = soup1.find_all()
        print(f"📊 Total HTML Elements: {len(all_elements)}")
        
        forms = soup1.find_all('form')
        print(f"📊 Forms Found: {len(forms)}")
        
        inputs = soup1.find_all('input')
        print(f"📊 Input Elements: {len(inputs)}")
        
        selects = soup1.find_all('select')
        print(f"📊 Select Elements: {len(selects)}")
        
        if not forms:
            error_msg = "❌ CRITICAL: No forms found on main page!"
            print(error_msg)
            send_telegram_message(error_msg)
            return
            
        # Analyze the main form in complete detail
        print(f"\n" + "-"*60)
        print("COMPLETE FORM ANALYSIS")
        print("-"*60)
        
        form1 = forms[0]  # Main form
        
        print(f"📋 Form Attributes:")
        for attr, value in form1.attrs.items():
            print(f"   {attr}: '{value}'")
        
        # Show ALL form children elements
        print(f"\n📋 ALL FORM ELEMENTS (including non-input elements):")
        form_children = form1.find_all()
        print(f"Total elements in form: {len(form_children)}")
        
        for i, elem in enumerate(form_children[:20], 1):  # Show first 20
            attrs_str = ', '.join([f"{k}='{v}'" for k, v in elem.attrs.items()])
            text_preview = elem.get_text()[:50].replace('\n', ' ').strip()
            print(f"   {i:2d}. <{elem.name}> {attrs_str} | text: '{text_preview}'")
        
        # Focus on form inputs/selects specifically
        print(f"\n📋 FORM INPUT/SELECT ELEMENTS:")
        form_inputs = form1.find_all(['input', 'select', 'textarea', 'button'])
        
        if not form_inputs:
            error_msg = "❌ CRITICAL: No input elements found in form!"
            print(error_msg)
            send_telegram_message(error_msg)
            return
            
        print(f"Found {len(form_inputs)} input/select elements:")
        
        for i, elem in enumerate(form_inputs, 1):
            print(f"\n   Element {i}: <{elem.name}>")
            print(f"      name: '{elem.get('name', 'NO NAME')}'")
            print(f"      id: '{elem.get('id', 'NO ID')}'")
            print(f"      type: '{elem.get('type', 'NO TYPE')}'")
            print(f"      value: '{elem.get('value', 'NO VALUE')}'")
            print(f"      class: '{elem.get('class', 'NO CLASS')}'")
            
            # For selects, show all options
            if elem.name == 'select':
                options = elem.find_all('option')
                print(f"      options: {len(options)} total")
                for j, opt in enumerate(options):
                    opt_value = opt.get('value', 'NO VALUE')
                    opt_text = opt.get_text().strip()
                    selected = " [SELECTED]" if opt.get('selected') else ""
                    print(f"         {j+1:2d}. value='{opt_value}' | text='{opt_text}'{selected}")
        
        # Find Office dropdown specifically
        print(f"\n" + "-"*40)
        print("OFFICE DROPDOWN SPECIFIC ANALYSIS")
        print("-"*40)
        
        # Try multiple ways to find Office dropdown
        office_methods = [
            ('by id="Office"', soup1.find('select', {'id': 'Office'})),
            ('by name="Office"', soup1.find('select', {'name': 'Office'})),
            ('by id contains "office"', soup1.find('select', attrs={'id': lambda x: x and 'office' in x.lower()})),
            ('by name contains "office"', soup1.find('select', attrs={'name': lambda x: x and 'office' in x.lower()}))
        ]
        
        office_select = None
        for method_name, result in office_methods:
            print(f"Searching {method_name}: {'FOUND' if result else 'NOT FOUND'}")
            if result and not office_select:
                office_select = result
        
        if not office_select:
            print("❌ CRITICAL: Office dropdown not found by any method!")
            
            # Show all selects to see what's available
            all_selects = soup1.find_all('select')
            print(f"\nAll select elements found ({len(all_selects)}):")
            for i, sel in enumerate(all_selects, 1):
                print(f"   {i}. name='{sel.get('name')}', id='{sel.get('id')}'")
                options = sel.find_all('option')
                print(f"      {len(options)} options, first few:")
                for opt in options[:3]:
                    print(f"         '{opt.get_text().strip()}'")
            
            send_telegram_message("❌ Office dropdown not found by any search method!")
            return
        
        print(f"✅ Office dropdown found!")
        print(f"   Method that worked: {[m[0] for m in office_methods if m[1] is office_select][0]}")
        print(f"   Element: <select name='{office_select.get('name')}' id='{office_select.get('id')}'/>")
        
        # Analyze Office options for KAIRO
        print(f"\n📋 Office Dropdown Options Analysis:")
        options = office_select.find_all('option')
        print(f"Total options: {len(options)}")
        
        kairo_option = None
        for i, option in enumerate(options, 1):
            opt_value = option.get('value', 'NO VALUE')
            opt_text = option.get_text().strip()
            has_kairo = 'KAIRO' in opt_text.upper()
            
            print(f"   {i:2d}. value='{opt_value}' | text='{opt_text}' {'← KAIRO MATCH!' if has_kairo else ''}")
            
            if has_kairo and not kairo_option:
                kairo_option = option
        
        if not kairo_option:
            print("❌ CRITICAL: KAIRO option not found!")
            send_telegram_message("❌ KAIRO option not found in Office dropdown!")
            return
        
        print(f"\n✅ KAIRO option found:")
        print(f"   Value: '{kairo_option.get('value')}'")
        print(f"   Text: '{kairo_option.get_text().strip()}'")
        
        # Step 2: Prepare form submission data
        print(f"\n" + "="*80)
        print("STEP 2: PREPARING FORM SUBMISSION DATA")
        print("="*80)
        
        form_data = {}
        print(f"Processing {len(form_inputs)} form elements for submission:")
        
        for i, elem in enumerate(form_inputs, 1):
            name = elem.get('name')
            elem_type = elem.get('type', elem.name)
            
            print(f"\n   Processing element {i}: <{elem.name}> name='{name}' type='{elem_type}'")
            
            if not name:
                print(f"      ⏭️  Skipping - no name attribute")
                continue
            
            if name == 'Office' or elem.get('id') == 'Office':
                form_data[name] = kairo_option.get('value')
                print(f"      ✅ SET: {name} = '{kairo_option.get('value')}' (KAIRO selected)")
                
            elif elem_type == 'hidden':
                value = elem.get('value', '')
                form_data[name] = value
                print(f"      🔒 SET: {name} = '{value}' (hidden field)")
                
            elif elem_type == 'submit':
                value = elem.get('value', 'Submit')
                form_data[name] = value
                print(f"      🔘 SET: {name} = '{value}' (submit button)")
                
            elif elem.name == 'select' and name != 'Office':
                # Handle other select elements
                selected_opt = elem.find('option', selected=True)
                if selected_opt:
                    value = selected_opt.get('value', '')
                    print(f"      📋 SET: {name} = '{value}' (selected option)")
                else:
                    first_opt = elem.find('option')
                    value = first_opt.get('value', '') if first_opt else ''
                    print(f"      📋 SET: {name} = '{value}' (first option - no default)")
                form_data[name] = value
                
            elif elem_type in ['text', 'email', 'tel', 'password']:
                value = elem.get('value', '')
                form_data[name] = value
                print(f"      📝 SET: {name} = '{value}' (text input)")
                
            elif elem_type == 'checkbox':
                if elem.get('checked'):
                    value = elem.get('value', 'on')
                    form_data[name] = value
                    print(f"      ☑️  SET: {name} = '{value}' (checked checkbox)")
                else:
                    print(f"      ☐ SKIP: {name} (unchecked checkbox)")
                    
            elif elem_type == 'radio':
                if elem.get('checked'):
                    value = elem.get('value', 'on')
                    form_data[name] = value
                    print(f"      🔘 SET: {name} = '{value}' (selected radio)")
                else:
                    print(f"      ⚪ SKIP: {name} (unselected radio)")
                    
            else:
                print(f"      ❓ UNKNOWN: {name} type='{elem_type}' - not handled")
        
        print(f"\n📤 FINAL FORM DATA TO SUBMIT:")
        if not form_data:
            print("   ❌ NO DATA TO SUBMIT!")
            send_telegram_message("❌ No form data prepared for submission!")
            return
            
        for key, value in sorted(form_data.items()):
            print(f"   '{key}': '{value}'")
        
        # Determine form action URL
        form_action = form1.get('action', '')
        print(f"\n🎯 Form Action URL Processing:")
        print(f"   Raw action attribute: '{form_action}'")
        
        if not form_action:
            form_action = response1.url
            print(f"   No action - using current URL: {form_action}")
        elif form_action.startswith('/'):
            form_action = "https://appointment.bmeia.gv.at" + form_action
            print(f"   Relative URL - converted to: {form_action}")
        elif not form_action.startswith('http'):
            form_action = "https://appointment.bmeia.gv.at/" + form_action
            print(f"   Path URL - converted to: {form_action}")
        else:
            print(f"   Absolute URL - using as-is: {form_action}")
        
        # Step 3: Submit the form
        print(f"\n" + "="*80)
        print("STEP 3: SUBMITTING FORM")
        print("="*80)
        
        print(f"🚀 Submitting to: {form_action}")
        print(f"📋 Method: POST")
        print(f"📦 Data: {len(form_data)} fields")
        
        print(f"\nWaiting 2 seconds before submission...")
        time.sleep(2)
        
        # Submit with detailed error handling
        try:
            response2 = session.post(form_action, data=form_data, timeout=30, allow_redirects=True)
            print(f"✅ Form submitted successfully")
        except requests.exceptions.RequestException as e:
            error_msg = f"❌ Form submission request failed: {e}"
            print(error_msg)
            send_telegram_message(error_msg)
            return
        
        print(f"\n📊 FORM SUBMISSION RESPONSE:")
        print(f"   Status Code: {response2.status_code}")
        print(f"   Final URL: {response2.url}")
        print(f"   Content Length: {len(response2.content)} bytes")
        print(f"   Content Type: {response2.headers.get('content-type', 'Unknown')}")
        
        # Check if we were redirected
        if len(response2.history) > 0:
            print(f"   Redirects: {len(response2.history)} redirect(s)")
            for i, redirect in enumerate(response2.history, 1):
                print(f"      {i}. {redirect.status_code} -> {redirect.url}")
        else:
            print(f"   Redirects: None")
        
        # Show response headers
        print(f"\n📋 Response Headers:")
        for header in ['content-type', 'location', 'set-cookie', 'server']:
            if header in response2.headers:
                value = response2.headers[header][:100] + "..." if len(response2.headers[header]) > 100 else response2.headers[header]
                print(f"   {header}: {value}")
        
        if response2.status_code != 200:
            error_msg = f"❌ Form submission failed: HTTP {response2.status_code}"
            print(error_msg)
            send_telegram_message(error_msg)
            return
        
        print(f"\nWaiting 3 seconds for page processing...")
        time.sleep(3)
        
        # Step 4: Analyze response page
        print(f"\n" + "="*80)
        print("STEP 4: ANALYZING RESPONSE PAGE")
        print("="*80)
        
        soup2 = BeautifulSoup(response2.content, 'html.parser')
        
        # Basic page info
        title2 = soup2.title.string.strip() if soup2.title else "No title"
        print(f"📄 Response Page Title: '{title2}'")
        
        # Compare titles to see if we moved
        if title == title2:
            print(f"⚠️  SAME TITLE as main page - might still be on same page!")
        else:
            print(f"✅ DIFFERENT TITLE - successfully navigated to new page!")
        
        # Look for CalendarId
        calendar_select = soup2.find('select', {'id': 'CalendarId'})
        print(f"\n🎯 CalendarId Search Result: {'✅ FOUND' if calendar_select else '❌ NOT FOUND'}")
        
        if calendar_select:
            options = calendar_select.find_all('option')
            print(f"   CalendarId has {len(options)} options:")
            for i, opt in enumerate(options[:5], 1):  # Show first 5
                print(f"      {i}. {opt.get_text().strip()}")
        
        # Show all elements with IDs
        elements_with_id = soup2.find_all(attrs={'id': True})
        print(f"\n📋 All Elements with ID attributes ({len(elements_with_id)}):")
        for elem in elements_with_id:
            elem_id = elem.get('id')
            print(f"   <{elem.name}> id='{elem_id}'")
        
        # Show all forms on response page
        response_forms = soup2.find_all('form')
        print(f"\n📋 Forms on Response Page ({len(response_forms)}):")
        for i, form in enumerate(response_forms, 1):
            action = form.get('action', 'No action')
            method = form.get('method', 'No method')
            inputs_count = len(form.find_all(['input', 'select']))
            print(f"   Form {i}: action='{action}', method='{method}', inputs={inputs_count}")
        
        # Look for error messages
        error_selectors = [
            ('class="message-error"', soup2.find_all(class_='message-error')),
            ('class contains "error"', soup2.find_all(attrs={'class': lambda x: x and any('error' in cls.lower() for cls in x)})),
            ('text contains "error"', soup2.find_all(string=lambda text: text and 'error' in text.lower())),
        ]
        
        print(f"\n🔍 Error Message Search:")
        found_errors = False
        for selector_desc, results in error_selectors:
            if results:
                found_errors = True
                print(f"   {selector_desc}: {len(results)} found")
                for i, result in enumerate(results[:3], 1):  # Show first 3
                    if hasattr(result, 'get_text'):
                        text = result.get_text().strip()
                    else:
                        text = str(result).strip()
                    print(f"      {i}. {text}")
            else:
                print(f"   {selector_desc}: None found")
        
        if not found_errors:
            print(f"   ✅ No obvious error messages found")
        
        # Show page text preview
        page_text = soup2.get_text()
        clean_text = ' '.join(page_text.split())
        print(f"\n📝 Response Page Text Preview (first 300 chars):")
        print(f"   {clean_text[:300]}...")
        
        # Final analysis
        print(f"\n" + "="*80)
        print("FINAL ANALYSIS")
        print("="*80)
        
        if calendar_select:
            result = "🎉 SUCCESS: CalendarId dropdown found! Form submission worked correctly."
            print(result)
            send_telegram_message(result)
        else:
            analysis = f"""❌ ANALYSIS: CalendarId not found

🔍 Investigation Results:
- Main page loaded: ✅
- Office dropdown found: ✅  
- KAIRO option found: ✅
- Form data prepared: ✅ ({len(form_data)} fields)
- Form submitted: ✅ (HTTP {response2.status_code})
- Page title changed: {'❌ No' if title == title2 else '✅ Yes'}

🎯 Most Likely Issues:
1. Form validation failed (staying on same page)
2. Missing required fields not detected
3. Website requires JavaScript/CSRF tokens
4. Need to handle session/cookies differently

📋 Next Steps:
1. Check if validation errors are hidden
2. Look for required fields we missed
3. Try accessing website manually to compare"""
            
            print(analysis)
            send_telegram_message(analysis[:1000])  # Truncate for Telegram
        
        print(f"\n✅ Full debug analysis completed at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
    except Exception as e:
        error_msg = f"❌ Full debug error: {str(e)}"
        print(error_msg)
        send_telegram_message(error_msg)

if __name__ == "__main__":
    perform_full_debug()