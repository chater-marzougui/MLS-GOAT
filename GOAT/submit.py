import requests
import os
import zipfile
import re
import torch
from tqdm import tqdm

EXPECTED_RANGE_ONE = set(range(0, 300))  # 0000 to 0299

CPU_API_URL = "http://20.49.50.218/api"

def _login(team_id, password):
    response = requests.post(f"{CPU_API_URL}/auth/login", json={"name": team_id, "password": password})
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")
    return response.json()["access_token"]


def challenge1(folder_path, team_id, password):
    print(f"Submitting Task 1 for team {team_id}...")

    # ---------- Validation ----------
    if not os.path.isdir(folder_path):
        raise ValueError("Invalid folder path")

    pattern = re.compile(r"^sample_(\d{4})\.pt$")
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

    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
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

    class ProgressFileWrapper:
        def __init__(self, filepath, mode='rb'):
            self.filepath = filepath
            self.file = open(filepath, mode)
            self.size = os.path.getsize(filepath)
            self.pbar = tqdm(total=self.size, unit='B', unit_scale=True, unit_divisor=1024)
            self.uploaded = 0

        def read(self, size=-1):
            chunk = self.file.read(size)
            if chunk:
                self.uploaded += len(chunk)
                self.pbar.update(len(chunk))
            return chunk

        def __len__(self):
            return self.size

        def close(self):
            self.pbar.close()
            self.file.close()

    headers = {"Authorization": f"Bearer {token}"}

    try:
        wrapped_file = ProgressFileWrapper(zip_filename)
        files = {"file": (zip_filename, wrapped_file, "application/zip")}
        resp = requests.post(
            f"{CPU_API_URL}/submit/task1",
            headers=headers,
            files=files
        )
        wrapped_file.close()
    except Exception as e:
        if os.path.exists(zip_filename):
            os.remove(zip_filename)
        raise e

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
        response = requests.post(
            f"{CPU_API_URL}/auth/login",
            json={"name": team_id, "password": password}
        )
        if response.status_code != 200:
            raise Exception(f"Login failed: {response.text}")
        token = response.json()["access_token"]
    except Exception as e:
        raise e
    
    try:
        response = requests.get(f"{CPU_API_URL}/gpu-server-ip")
        if response.status_code != 200:
            raise Exception(f"Failed to get GPU server IP: {response.text}")
        GPU_API_URL = response.json()["gpu_server_ip"]
    except Exception as e:
        raise e

    # Submit directly to GPU server
    print("Uploading model to GPU server...")

    class ProgressFileWrapper:
        def __init__(self, filepath, mode='rb'):
            self.filepath = filepath
            self.file = open(filepath, mode)
            self.size = os.path.getsize(filepath)
            self.pbar = tqdm(total=self.size, unit='B', unit_scale=True, unit_divisor=1024)
            self.uploaded = 0

        def read(self, size=-1):
            chunk = self.file.read(size)
            if chunk:
                self.uploaded += len(chunk)
                self.pbar.update(len(chunk))
            return chunk

        def __len__(self):
            return self.size

        def close(self):
            self.pbar.close()
            self.file.close()
    
    try:
        wrapped_file = ProgressFileWrapper(model_path)
        files = {'file': (os.path.basename(model_path), wrapped_file, 'application/octet-stream')}
        data = {'team_token': token, 'batch_size': 8}
        
        resp = requests.post(
            f"{GPU_API_URL}/submit/task2",
            files=files,
            data=data
        )
        wrapped_file.close()
    except Exception as e:
        raise e
        
    if resp.status_code == 202:
        data = resp.json()
        print(f"✅ Submission Queued! Submission ID: {data['submission_id']}")
        print(f"Queue Position: {data['queue_position']}")
        return data
    else:
        print(f"❌ Submission Failed: {resp.text}")
        return None