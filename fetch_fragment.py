import requests
from bs4 import BeautifulSoup
import re

url = "https://github.com/defunkt?action=show&controller=profiles&tab=contributions&user_id=defunkt"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest'
}
resp = requests.get(url, headers=headers)
with open("fragment.html", "w", encoding="utf-8") as f:
    f.write(resp.text)

soup = BeautifulSoup(resp.content, 'html.parser')
calendar = soup.find('table', class_='ContributionCalendar-grid')
print(f"Calendar found: {calendar is not None}")
if calendar:
    days = calendar.find_all(class_=re.compile(r'ContributionCalendar-day'))
    print(f"Days found: {len(days)}")
    # Try parsing
    total_count = 0
    for day in days:
        sr_only = day.find('span', class_='sr-only')
        if sr_only:
            text_content = sr_only.get_text().strip()
            print(f"Sample text: {text_content}") # Print first one
            break
