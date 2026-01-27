from bs4 import BeautifulSoup
import re

with open("fragment.html", "r", encoding="utf-8") as f:
    content = f.read()

soup = BeautifulSoup(content, 'html.parser')
tooltips = soup.find_all('tool-tip')
print(f"Tooltips found: {len(tooltips)}")
total_count = 0
for tt in tooltips:
    text = tt.get_text().strip()
    if "contribution" in text:
        # "No contributions on..." or "X contributions on..."
        # "1 contribution on..."
        match = re.search(r'^(\d+)\s+contribution', text)
        if match:
            count = int(match.group(1))
            total_count += count
            print(f"Found {count} in '{text}'")
        elif "No contributions" in text:
            pass
        else:
             # Check if starts with number?
             parts = text.split()
             if parts and parts[0].isdigit():
                 total_count += int(parts[0])
                 print(f"Found {parts[0]} (fallback) in '{text}'")

print(f"Total: {total_count}")
