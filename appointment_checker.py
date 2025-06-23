import requests
from bs4 import BeautifulSoup

session = requests.Session()
url = "https://appointment.bmeia.gv.at"

# 1. Load page
resp = session.get(url)
soup = BeautifulSoup(resp.text, "html.parser")

# 2. Find form and Office select
form = soup.find("form")
office_select = form.find("select", {"name": "Office"})
kairo_option = None
for opt in office_select.find_all("option"):
    if "KAIRO" in opt.text.upper():
        kairo_option = opt
        break
assert kairo_option, "KAIRO option not found"

office_value = kairo_option.get("value")
print(f"KAIRO value: '{office_value}'")

# 3. Build form data (include all hidden and submit fields)
form_data = {}
for inp in form.find_all("input"):
    if inp.get("type") == "hidden" or inp.get("type") == "submit":
        form_data[inp["name"]] = inp.get("value", "")

form_data["Office"] = office_value
print("Form data to submit:", form_data)

# 4. Form action
action = form.get("action")
if action.startswith("/"):
    action_url = url + action
else:
    action_url = action
print("Form action URL:", action_url)

# 5. POST request
post_resp = session.post(action_url, data=form_data)
post_soup = BeautifulSoup(post_resp.text, "html.parser")
print("Response page title:", post_soup.title.string if post_soup.title else "No title")

# 6. Check if CalendarId exists
calendar = post_soup.find("select", {"id": "CalendarId"})
print("CalendarId found?", bool(calendar))