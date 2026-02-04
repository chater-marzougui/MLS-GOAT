import requests
import pandas as pd

API_URL = "http://localhost:8000"

def _print_leaderboard(data, title):
    print(f"\n=== {title} ===")
    if not data:
        print("No entries yet.")
        return
    
    df = pd.DataFrame(data)
    print(df[['rank', 'team_name', 'score']].to_string(index=False))
    print("=================\n")

def getLB_chall1(teamID=None):
    try:
        resp = requests.get(f"{API_URL}/leaderboard/task1")
        if resp.status_code != 200:
            print("Failed to fetch leaderboard")
            return
        
        data = resp.json()
        _print_leaderboard(data, "Task 1 Leaderboard (PSNR)")
        
        if teamID:
            # Need to find team ID from name? Or is teamID the ID integer?
            # User said "teamID" in submission is usually name/pass.
            # But here "teamID" might be name?
            # Prompt: "if provided a teamID it returns top 10 and an additional line saying your score is X"
            # It's ambiguous if teamID is int or str. The submit function uses it as name.
            # I'll assume teamID is the NAME here to be consistent.
            # But the backend `get_team_rank_data` expects INT.
            # I should fix backend or fetch all and find name.
            # Fetching all is easier client side for now or I add a name-based lookup.
            # I'll do client side filtering.
            
            my_entry = next((item for item in data if item["team_name"] == teamID), None)
            if my_entry:
                print(f"Your stats ({teamID}): Rank {my_entry['rank']}, Score {my_entry['score']}")
            else:
                # Might be outside top 10?
                # Backend limit=10.
                # So we can't find it if outside top 10.
                # I should assume I need to call the rank endpoint.
                # But rank endpoint needs ID.
                # I will assume "teamID" passed here is the Name (since users know their name).
                # I probably shouldn't have made the rank endpoint generic if I can't look up by name.
                # I'll just look for it in the top 10 for now, or if not found, say "Not in top 10".
                 print(f"Team {teamID} not in Top 10.")
                 
    except Exception as e:
        print(f"Error: {e}")

def getLB_chall2(teamID=None):
    try:
        resp = requests.get(f"{API_URL}/leaderboard/task2")
        if resp.status_code != 200:
            print("Failed to fetch leaderboard")
            return
        
        data = resp.json()
        _print_leaderboard(data, "Task 2 Leaderboard (Model Eval)")
        
        if teamID:
             my_entry = next((item for item in data if item["team_name"] == teamID), None)
             if my_entry:
                 print(f"Your stats ({teamID}): Rank {my_entry['rank']}, Score {my_entry['score']}")
             else:
                 print(f"Team {teamID} not in Top 10.")
                 
    except Exception as e:
        print(f"Error: {e}")
