import requests
url = "https://github.com/defunkt?action=show&controller=profiles&tab=contributions&user_id=defunkt"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest'
}
try:
    resp = requests.get(url, headers=headers)
    print(f"Status: {resp.status_code}")
    if "ContributionCalendar" in resp.text:
        print("Found ContributionCalendar!")
    else:
        print("ContributionCalendar NOT found.")
        # print(resp.text[:500])
except Exception as e:
    print(e)
