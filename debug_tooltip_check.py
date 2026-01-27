from bs4 import BeautifulSoup
import re

with open("fragment.html", "r", encoding="utf-8") as f:
    content = f.read()

soup = BeautifulSoup(content, 'html.parser')
tooltips = soup.find_all('tool-tip')
print(f"Tooltips found: {len(tooltips)}")
for tt in tooltips:
    text = tt.get_text().strip()
    if "No contributions" not in text:
        print(f"NON-ZERO: '{text}'")
