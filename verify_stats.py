import requests
from app import get_github_stats

test_usernames = ['torvalds', 'google', 'microsoft']

print(f"{'Username':<15} | {'Repos':<6} | {'Yearly':<8} | {'Daily':<6} | {'Stars':<8} | {'Forks':<8}")
print("-" * 65)

for username in test_usernames:
    stats = get_github_stats(username)
    if stats.get('error'):
        print(f"{username:<15} | Error: {stats['error']}")
    else:
        print(f"{username:<15} | {stats['public_repos']:<6} | {stats['contributions_last_year']:<8} | {stats['contributions_today']:<6} | {stats['total_stars']:<8} | {stats['total_forks']:<8}")
