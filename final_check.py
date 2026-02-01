from bs4 import BeautifulSoup
import re

def get_counts(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    h2_text = ""
    h2 = soup.find('h2', class_=re.compile(r'f4 text-normal'))
    if h2:
        h2_text = h2.get_text(strip=True)
    
    calendar = soup.find('table', class_='ContributionCalendar-grid')
    if not calendar:
        calendar = soup.find('div', class_='js-calendar-graph')
    
    total_from_grid = 0
    if calendar:
        tooltips = calendar.find_all('tool-tip')
        if tooltips:
            for tt in tooltips:
                match = re.search(r'(\d+)\s+contribution', tt.get_text())
                if match:
                    total_from_grid += int(match.group(1))
        else:
            days = calendar.find_all(class_=re.compile(r'ContributionCalendar-day'))
            for day in days:
                sr_only = day.find('span', class_='sr-only')
                if sr_only:
                    match = re.search(r'(\d+)\s+contribution', sr_only.get_text())
                    if match:
                        total_from_grid += int(match.group(1))
    
    return h2_text, total_from_grid

for f in ['fragment.html', 'torvalds_fragment.html']:
    h2, grid = get_counts(f)
    print(f"{f}: H2='{h2}', Grid Sum={grid}")
