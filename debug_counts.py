from bs4 import BeautifulSoup
import re
import os

def count_contributions(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Method 1: H2 tag
    h2_tags = soup.find_all('h2')
    h2_count = 0
    for h2 in h2_tags:
        text = h2.get_text().strip()
        if 'contributions' in text and 'last year' in text:
            # Handle cases like "3,119 contributions" or "0 contributions"
            # It might have leading/trailing whitespace or newlines
            match = re.search(r'([\d,]+)\s+contribution', text)
            if match:
                num_str = match.group(1).replace(',', '')
                h2_count = int(num_str)
                print(f"H2 Method found: {h2_count}")
                break

    # Method 2: Tooltips
    calendar = soup.find('table', class_='ContributionCalendar-grid')
    if not calendar:
        calendar = soup.find('div', class_='js-calendar-graph')
    
    tooltip_count = 0
    if calendar:
        qt_tooltips = calendar.find_all('tool-tip')
        for tt in qt_tooltips:
            txt = tt.get_text().strip()
            match = re.search(r'(\d+)\s+contribution', txt)
            if match:
                tooltip_count += int(match.group(1))
    
    # Method 3: sr-only spans
    sr_only_count = 0
    non_zero_days = []
    if calendar:
        days = calendar.find_all(class_=re.compile(r'ContributionCalendar-day'))
        for day in days:
            # Check data-level attribute directly
            level = day.get('data-level')
            date = day.get('data-date')
            if level and level != '0':
                non_zero_days.append({'date': date, 'level': level})

            sr_only = day.find('span', class_='sr-only')
            if sr_only:
                text_content = sr_only.get_text().strip()
                match_count = re.search(r'(\d+)\s+contribution', text_content)
                if match_count:
                    sr_only_count += int(match_count.group(1))
                elif "No contributions" not in text_content:
                    first_word = text_content.split()[0]
                    if first_word.isdigit():
                        sr_only_count += int(first_word)

    # Method 4: SVG rects
    svg_rect_count = 0
    rects = soup.find_all('rect', class_='day')
    for rect in rects:
        if rect.has_attr('data-count'):
            svg_rect_count += int(rect['data-count'])

    return {
        'h2': h2_count,
        'tooltips': tooltip_count,
        'sr_only': sr_only_count,
        'svg_rects': svg_rect_count,
        'non_zero_days_count': len(non_zero_days),
        'some_non_zero_days': non_zero_days[:5]
    }

if __name__ == "__main__":
    files = ['fragment.html', 'torvalds_fragment.html']
    for f in files:
        if not os.path.exists(f): 
            print(f"File {f} not found")
            continue
        print(f"\n--- Analyzing {f} ---")
        counts = count_contributions(f)
        for k, v in counts.items():
            print(f"{k}: {v}")
