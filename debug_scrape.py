from app import get_github_stats
print("Starting stats collection for torvalds...")
stats = get_github_stats('torvalds')
print(f"Contributions: {stats['contributions_last_year']}")
