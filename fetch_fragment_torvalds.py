import requests
from bs4 import BeautifulSoup
import re

# Torvalds fragment URL
url = "https://github.com/torvalds?action=show&controller=profiles&tab=contributions&user_id=torvalds"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest'
}
resp = requests.get(url, headers=headers)
with open("torvalds_fragment.html", "w", encoding="utf-8") as f:
    f.write(resp.text)

soup = BeautifulSoup(resp.content, 'html.parser')
tooltips = soup.find_all('tool-tip')
print(f"Tooltips found: {len(tooltips)}")

total = 0
for tt in tooltips:
    text = tt.get_text().strip()
    # match = re.search(r'^(\d+)\s+contribution', text)
    # Be more flexible
    match = re.search(r'(\d+)\s+contribution', text)
    if match:
        count = int(match.group(1))
        # print(f"Found {count}")
        total += count

print(f"Total: {total}")
