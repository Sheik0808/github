import requests
import re

try:
    print("Sending request...")
    resp = requests.post("http://127.0.0.1:5002/analyze", data={"github_link": "torvalds"})
    print(f"Status: {resp.status_code}")
    
    content = resp.text
    with open("output.html", "w", encoding="utf-8") as f:
        f.write(content)
        
    match = re.search(r'<div class="stat-value">(\d+)</div>\s*<div class="stat-label">Contributions \(Year\)</div>', content)
    if match:
        print(f"Contributions found: {match.group(1)}")
        if int(match.group(1)) > 0:
            print("SUCCESS: Contributions are greater than 0.")
        else:
            print("FAILURE: Contributions are 0.")
    else:
        # Fallback regex if newlines vary
        match = re.search(r'Contributions \(Year\)', content)
        if match:
            print("Found label, looking for value...")
            # finding the value before it
            # implementation omitted for brevity, inspect file/grep
            pass
        else:
            print("FAILURE: Could not find Contributions label.")

except Exception as e:
    print(e)
