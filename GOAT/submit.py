import requests
import os
import zipfile
import shutil

API_URL = "https://framing-innocent-ira-ends.trycloudflare.com"

def _login(team_id, password):
    # team_id in prompt is likely the name? "teamID" string.
    # Our Auth uses name/password.
    response = requests.post(f"{API_URL}/auth/login", json={"name": team_id, "password": password})
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")
    return response.json()["access_token"]

def challenge1(folder_path, team_id, password):
    print(f"Submitting Task 1 for team {team_id}...")
    
    # Validation
    if not os.path.isdir(folder_path):
        raise ValueError("Invalid folder path")
    
    # Check images
    files = [f for f in os.listdir(folder_path) if f.endswith('.pt')]
    if not files:
        raise ValueError("No .pt files found in folder")
    
    import torch
    print("Validating file dimensions...")
    for f in files:
        try:
            t = torch.load(os.path.join(folder_path, f))
            if t.shape != (29, 96, 96):
                raise ValueError(f"File {f} has Invalid shape {t.shape}. Expected (29, 96, 96)")
        except Exception as e:
            raise ValueError(f"Failed to load/check {f}: {e}")
    
    # Zip
    zip_filename = f"{team_id}_task1.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, folder_path)
                zipf.write(filepath, arcname)
                
    # Login
    try:
        token = _login(team_id, password)
    except Exception as e:
        if os.path.exists(zip_filename):
            os.remove(zip_filename)
        raise e
        
    # Upload
    headers = {"Authorization": f"Bearer {token}"}
    with open(zip_filename, 'rb') as f:
        files = {'file': (zip_filename, f, 'application/zip')}
        resp = requests.post(f"{API_URL}/submit/task1", headers=headers, files=files)
        
    # Cleanup
    if os.path.exists(zip_filename):
        os.remove(zip_filename)
        
    if resp.status_code == 200:
        data = resp.json()
        print(f"Submission Successful! Score: {data['public_score']}")
        return data
    else:
        print(f"Submission Failed: {resp.text}")
        return None

def challenge2(model_path, team_id, password):
    print(f"Submitting Task 2 for team {team_id}...")
    
    if not os.path.isfile(model_path) or not model_path.endswith('.onnx'):
        raise ValueError("Invalid .onnx file")
        
    try:
        token = _login(team_id, password)
    except Exception as e:
        raise e
        
    headers = {"Authorization": f"Bearer {token}"}
    with open(model_path, 'rb') as f:
        files = {'file': (os.path.basename(model_path), f, 'application/octet-stream')}
        resp = requests.post(f"{API_URL}/submit/task2", headers=headers, files=files)
        
    if resp.status_code == 200:
        data = resp.json()
        print(f"Submission Successful! Score: {data['public_score']}")
        return data
    else:
        print(f"Submission Failed: {resp.text}")
        return None
