import requests
import os
import zipfile
import re
import torch
from tqdm import tqdm

EXPECTED_RANGE_ONE = set(range(0, 229))

API_URL = "https://framing-innocent-ira-ends.trycloudflare.com"

def _login(team_id, password):
    response = requests.post(f"{API_URL}/auth/login", json={"name": team_id, "password": password})
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")
    return response.json()["access_token"]



def challenge1(folder_path, team_id, password):
    print(f"Submitting Task 1 for team {team_id}...")

    # ---------- Validation ----------
    if not os.path.isdir(folder_path):
        raise ValueError("Invalid folder path")

    pattern = re.compile(r"^part1_(\d{6})\.pt$")
    matched_files = {}
    bad_files = []

    for f in os.listdir(folder_path):
        m = pattern.match(f)
        if not m:
            bad_files.append(f)
            continue

        idx = int(m.group(1))
        if idx not in EXPECTED_RANGE_ONE:
            bad_files.append(f)
            continue

        matched_files[idx] = f

    missing = sorted(EXPECTED_RANGE_ONE - matched_files.keys())

    if bad_files:
        raise ValueError(
            f"Invalid filenames detected:\n" + "\n".join(sorted(bad_files))
        )

    if missing:
        raise ValueError(
            f"Missing required files:\n{missing}"
        )

    print("✅ All filenames validated")

    # ---------- Shape check ----------
    print("Validating tensor dimensions...")
    for idx in tqdm(sorted(matched_files)):
        f = matched_files[idx]
        path = os.path.join(folder_path, f)
        try:
            t = torch.load(path)
            if t.shape != (29, 96, 96):
                raise ValueError(f"{f}: invalid shape {t.shape}")
        except Exception as e:
            raise ValueError(f"Failed to load/check {f}: {e}")

    print("✅ All tensors have correct shape")

    # ---------- Zip ----------
    zip_filename = f"{team_id}_task1.zip"
    print("Zipping files...")

    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for idx in tqdm(sorted(matched_files)):
            f = matched_files[idx]
            path = os.path.join(folder_path, f)
            zipf.write(path, arcname=f)

    # ---------- Login ----------
    try:
        token = _login(team_id, password)
    except Exception:
        if os.path.exists(zip_filename):
            os.remove(zip_filename)
        raise

    # ---------- Upload with progress ----------
    print("Uploading submission...")

    class TqdmFile:
        def __init__(self, fileobj, total):
            self.fileobj = fileobj
            self.pbar = tqdm(total=total, unit="B", unit_scale=True)

        def read(self, size=-1):
            data = self.fileobj.read(size)
            self.pbar.update(len(data))
            return data

        def close(self):
            self.pbar.close()
            self.fileobj.close()

    total_size = os.path.getsize(zip_filename)
    headers = {"Authorization": f"Bearer {token}"}

    with open(zip_filename, "rb") as f:
        wrapped = TqdmFile(f, total_size)
        files = {"file": (zip_filename, wrapped, "application/zip")}
        resp = requests.post(
            f"{API_URL}/submit/task1",
            headers=headers,
            files=files
        )
        wrapped.close()

    # ---------- Cleanup ----------
    if os.path.exists(zip_filename):
        os.remove(zip_filename)

    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Submission Successful! Score: {data['public_score']}")
        return data
    else:
        print(f"❌ Submission Failed: {resp.text}")
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
