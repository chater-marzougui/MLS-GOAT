import requests
import pandas as pd

API_URL = "http://20.49.50.218/api"

def _print_leaderboard(data, title):
    print(f"\n=== {title} ===")
    if not data:
        print("No entries yet.")
        return
    
    df = pd.DataFrame(data)
    print(df[['rank', 'team_name', 'score']].to_string(index=False))
    print("=================\n")
def getLB_chall1(team_name=None):
    try:
        url = f"{API_URL}/leaderboard/task1"
        params = {"team_name": team_name} if team_name else {}
        resp = requests.get(url, params=params)
        
        if resp.status_code != 200:
            print("Failed to fetch leaderboard")
            return
        
        data = resp.json()
        
        # Separate top 10 from user's entry
        top_10 = data[:10]
        user_entry = data[10] if len(data) > 10 else None
        
        _print_leaderboard(top_10, "Task 1 Leaderboard (PSNR) - Top 10")
        
        if team_name:
            my_entry = next((item for item in data if item["team_name"] == team_name), None)
            if my_entry:
                if my_entry['rank'] <= 10:
                    print(f"Your stats ({team_name}): Rank {my_entry['rank']}, Score {my_entry['score']}")
                else:
                    print(f"\nYour stats ({team_name}): Rank {my_entry['rank']}, Score {my_entry['score']}")
            else:
                print(f"Team {team_name} has no submissions yet.")
                 
    except Exception as e:
        print(f"Error: {e}")

def getLB_chall2(team_name=None):
    try:
        url = f"{API_URL}/leaderboard/task2"
        params = {"team_name": team_name} if team_name else {}
        resp = requests.get(url, params=params)
        
        if resp.status_code != 200:
            print("Failed to fetch leaderboard")
            return
        
        data = resp.json()
        
        # Separate top 10 from user's entry
        top_10 = data[:10]
        
        _print_leaderboard(top_10, "Task 2 Leaderboard (Model Eval) - Top 10")
        
        if team_name:
            my_entry = next((item for item in data if item["team_name"] == team_name), None)
            if my_entry:
                if my_entry['rank'] <= 10:
                    print(f"Your stats ({team_name}): Rank {my_entry['rank']}, Score {my_entry['score']}")
                else:
                    print(f"\nYour stats ({team_name}): Rank {my_entry['rank']}, Score {my_entry['score']}")
            else:
                print(f"Team {team_name} has no submissions yet.")
                 
    except Exception as e:
        print(f"Error: {e}")