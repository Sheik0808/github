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

def get_github_stats(username):
    stats = {
        'username': username,
        'public_repos': 0,
        'followers': 0,
        'following': 0,
        'total_stars': 0,
        'total_forks': 0,
        'contributions_last_year': 0,
        'languages': {},
        'avatar_url': '',
        'profile_url': f'https://github.com/{username}',
        'error': None
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # 1. Get User Info (Public API)
    try:
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

        # 2. Get Repos Info (Public API)
        repos_url = f"https://api.github.com/users/{username}/repos?per_page=100"
        repo_response = requests.get(repos_url, headers=headers)
        if repo_response.status_code == 200:
            repos = repo_response.json()
            for repo in repos:
                stats['total_stars'] += repo.get('stargazers_count', 0)
                stats['total_forks'] += repo.get('forks_count', 0)
                lang = repo.get('language')
                if lang:
                    stats['languages'][lang] = stats['languages'].get(lang, 0) + 1
        
        # 3. Scrape Contributions
        # Try multiple selectors as GitHub structure varies
        profile_url = f"https://github.com/{username}"
        profile_response = requests.get(profile_url, headers=headers)
        if profile_response.status_code == 200:
            soup = BeautifulSoup(profile_response.content, 'html.parser')
            
            # Method 1: Look for the specific H2 that says "contributions in the last year"
            h2_tags = soup.find_all('h2')
            found_contrib = False
            for h2 in h2_tags:
                text = h2.get_text().strip()
                if 'contributions' in text and 'last year' in text:
                    num_str = text.split()[0].replace(',', '')
                    if num_str.isdigit():
                        stats['contributions_last_year'] = int(num_str)
                        found_contrib = True
                    break
            
            # Method 2: Count the "green boxes" (contribution calendar) directly
            # This is what the user specifically asked for "count the contribution ion green box"
            if not found_contrib or stats['contributions_last_year'] == 0:
                calendar = soup.find('table', class_='ContributionCalendar-grid')
                if not calendar:
                    # Fallback for old structure or different view
                    calendar = soup.find('div', class_='js-calendar-graph')
                
                if calendar:
                    # The contribution cells are usually 'td' or 'rect' with 'data-level' or 'data-count'
                    print(f"Found contribution calendar. Parsing days...")
                    
                    days = calendar.find_all(class_=re.compile(r'ContributionCalendar-day'))
                    total_count = 0
                    for day in days:
                        # Try to find the count in the sr-only span (screen reader text)
                        sr_only = day.find('span', class_='sr-only')
                        if sr_only:
                           text_content = sr_only.get_text().strip()
                           # Format examples: "No contributions on..." or "5 contributions on..."
                           match_count = re.search(r'(\d+)\s+contribution', text_content)
                           if match_count:
                               count = int(match_count.group(1))
                               total_count += count
                           elif "No contributions" not in text_content:
                               # Fallback: check if starts with number
                               first_word = text_content.split()[0]
                               if first_word.isdigit():
                                   total_count += int(first_word)
                    
                    print(f"Calculated total contributions from calendar: {total_count}")
                    if total_count > 0:
                        stats['contributions_last_year'] = total_count
                        found_contrib = True

                # Method 3: Parsing the SVG rects (Old style if still present/fallback)
                if not found_contrib:
                     rects = soup.find_all('rect', class_='day')
                     if rects:
                         print("Found SVG rects (old style). Parsing...")
                         total_count = 0
                         for rect in rects:
                             if rect.has_attr('data-count'):
                                 total_count += int(rect['data-count'])
                         
                         print(f"Calculated total contributions from SVG: {total_count}")
                         if total_count > 0:
                             stats['contributions_last_year'] = total_count

    except Exception as e:
        print(f"Scraping error: {e}")
        stats['error'] = f"An error occurred: {str(e)}"
    
    return stats

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    username = None
    
    # Check if direct link or username provided
    github_input = request.form.get('github_link')
    if github_input:
        if 'github.com/' in github_input:
            username = extract_github_username(github_input)
        else:
            username = github_input # Assume they typed just the username

    # Check if file uploaded
    if not username and 'file_upload' in request.files:
        file = request.files['file_upload']
        if file.filename != '':
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            text_content = extract_text_from_file(filepath, file.filename)
            if text_content is None:
                flash("Error reading the file. Please try a different file.", 'error')
                return redirect(url_for('index'))
            
            username = extract_github_username(text_content)
            
            # Clean up file in finally block or check permissions
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Error removing file {filepath}: {e}")

    if username:
        stats = get_github_stats(username)
        if stats['error']:
            flash(stats['error'], 'error')
            return redirect(url_for('index'))
        return render_template('dashboard.html', stats=stats)
    else:
        flash("Could not detect a GitHub username or Link.", 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)
