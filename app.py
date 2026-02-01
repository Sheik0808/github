import os
import re
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import PyPDF2
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Change this for production
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def extract_github_username(text):
    # Regex to find github.com/username
    # Improved: Case insensitive, handles http/s, www, and trailing slashes
    match = re.search(r'github\.com\/([a-zA-Z0-9-]+)', text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def extract_text_from_file(filepath, filename):
    text = ""
    try:
        if filename.endswith('.pdf'):
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(filepath, engine='openpyxl')
            text = df.to_string()
        elif filename.endswith('.xls'):
            # Basic fallback for xls if engine not specified, usually requires xlrd
            df = pd.read_excel(filepath) 
            text = df.to_string()
        elif filename.endswith('.txt'):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
        return None # Return None to signal error
    return text

def get_github_stats(username, token=None):
    stats = {
        'username': username,
        'public_repos': 0,
        'followers': 0,
        'following': 0,
        'total_stars': 0,
        'total_forks': 0,
        'contributions_last_year': 0,
        'contributions_today': 0,
        'languages': {},
        'avatar_url': '',
        'profile_url': f'https://github.com/{username}',
        'error': None
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    if token:
        headers['Authorization'] = f'token {token}'

    try:
        # 1. Get User Info (Public API)
        user_url = f"https://api.github.com/users/{username}"
        response = requests.get(user_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            stats['public_repos'] = data.get('public_repos', 0)
            stats['followers'] = data.get('followers', 0)
            stats['following'] = data.get('following', 0)
            stats['avatar_url'] = data.get('avatar_url', '')
        elif response.status_code == 404:
            stats['error'] = "User not found"
            return stats
        elif response.status_code == 403: # Rate limited
             stats['error'] = "API Rate Limit Exceeded"
             return stats

        # 2. Get Repos Info (Public API) - With Pagination
        page = 1
        while True:
            repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&page={page}"
            repo_response = requests.get(repos_url, headers=headers)
            if repo_response.status_code == 200:
                repos = repo_response.json()
                if not repos:
                    break
                for repo in repos:
                    # Filter for owned repos if needed, but here we count all public ones
                    stats['total_stars'] += repo.get('stargazers_count', 0)
                    stats['total_forks'] += repo.get('forks_count', 0)
                    lang = repo.get('language')
                    if lang:
                        stats['languages'][lang] = stats['languages'].get(lang, 0) + 1
                if len(repos) < 100:
                    break
                page += 1
            else:
                break
        
        # 3. Scrape Contributions
        profile_url = f"https://github.com/{username}"
        profile_response = requests.get(profile_url, headers=headers)
        if profile_response.status_code == 200:
            soup = BeautifulSoup(profile_response.content, 'html.parser')
            
            # Method 1: Total contributions in the last year (H2)
            # Try specific ID first
            h2_contrib = soup.find('h2', id='js-contribution-activity-description')
            if not h2_contrib:
                # Fallback to searching all h2 tags
                h2_tags = soup.find_all('h2')
                for h2 in h2_tags:
                    if 'contributions' in h2.get_text().lower() and 'last year' in h2.get_text().lower():
                        h2_contrib = h2
                        break
            
            if h2_contrib:
                text = h2_contrib.get_text().strip()
                # Use regex to find the first number (handles "3,119", "0", etc.)
                match = re.search(r'([\d,]+)', text)
                if match:
                    stats['contributions_last_year'] = int(match.group(1).replace(',', ''))
            
            # Method 2: Scrape calendar for accurate counts and today's stats
            calendar = soup.find('table', class_='ContributionCalendar-grid')
            if not calendar:
                calendar = soup.find(class_='js-calendar-graph')

            if not calendar:
                 # Check for include-fragment or data-graph-url
                 frags = soup.find_all(['include-fragment', 'div'], src=True) or soup.find_all('div', attrs={'data-graph-url': True})
                 for frag in frags:
                     src = frag.get('src') or frag.get('data-graph-url')
                     if src and 'contributions' in src:
                         try:
                             frag_url = f"https://github.com{src}" if src.startswith('/') else src
                             frag_resp = requests.get(frag_url, headers=headers)
                             if frag_resp.status_code == 200:
                                 frag_soup = BeautifulSoup(frag_resp.content, 'html.parser')
                                 calendar = frag_soup.find('table', class_='ContributionCalendar-grid') or frag_soup.find(class_='js-calendar-graph')
                                 if calendar:
                                     break
                         except Exception as e:
                             print(f"Error fetching fragment: {e}")
            
            if calendar:
                total_count = 0
                today_count = 0
                
                # Check tooltips
                tooltips = calendar.find_all('tool-tip')
                if tooltips:
                    for tt in tooltips:
                        txt = tt.get_text().strip()
                        match = re.search(r'(\d+)\s+contribution', txt)
                        if match:
                            count = int(match.group(1))
                            total_count += count
                            today_count = count 
                
                # Check sr-only or data-count
                if total_count == 0:
                    days = calendar.find_all(class_=re.compile(r'ContributionCalendar-day'))
                    for day in days:
                        count = 0
                        sr_only = day.find('span', class_='sr-only')
                        if sr_only:
                           match_count = re.search(r'(\d+)\s+contribution', sr_only.get_text())
                           if match_count:
                               count = int(match_count.group(1))
                           elif "No contributions" not in sr_only.get_text():
                               first_word = sr_only.get_text().strip().split()[0]
                               if first_word.isdigit():
                                   count = int(first_word)
                        else:
                            cnt = day.get('data-count')
                            if cnt:
                                count = int(cnt)
                        
                        total_count += count
                        today_count = count # Last one
                
                if total_count > 0 and stats['contributions_last_year'] == 0:
                    stats['contributions_last_year'] = total_count
                stats['contributions_today'] = today_count

    except Exception as e:
        print(f"Scraping error: {e}")
        stats['error'] = f"An error occurred: {str(e)}"
    
    return stats

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
@app.route('/analyze', methods=['POST'])
def analyze():
    usernames = []
    
    # Check if direct link or username provided (handle multiline/comma separated)
    github_input = request.form.get('github_link')
    if github_input:
        parts = re.split(r'[\n,]+', github_input)
        for part in parts:
            part = part.strip()
            if part:
                u = extract_github_username(part) if 'github.com' in part else part
                if u:
                    usernames.append(u)

    # Check if file uploaded
    if 'file_upload' in request.files:
        file = request.files['file_upload']
        if file.filename != '':
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            text_content = extract_text_from_file(filepath, file.filename)
            
            # Clean up file
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Error removing file {filepath}: {e}")

            if text_content:
                # Try to find all github links in text
                found_usernames = re.findall(r'github\.com/([a-zA-Z0-9-]+)', text_content)
                if found_usernames:
                    usernames.extend(found_usernames)
                else:
                    # Fallback single extraction if regex fails
                    u = extract_github_username(text_content)
                    if u: usernames.append(u)
            else:
                flash("Error reading the file or empty file.", 'error')

    # Remove duplicates
    usernames = list(set(usernames))
    
    if not usernames:
         flash("Could not detect any GitHub usernames or Links.", 'error')
         return redirect(url_for('index'))

    # Check environment variable for token if available (optional/backend only)
    github_token = os.environ.get('GITHUB_TOKEN')

    stats_list = []
    for username in usernames:
        s = get_github_stats(username, token=github_token)
        stats_list.append(s)

    return render_template('dashboard.html', stats_list=stats_list)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
