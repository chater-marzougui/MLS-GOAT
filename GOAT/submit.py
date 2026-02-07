import requests
import os
import zipfile
import re
import torch
import time
from tqdm import tqdm

EXPECTED_RANGE_ONE = set(range(0, 300))  # 0000 to 0299

CPU_API_URL = "https://mls-goat.eastus2.cloudapp.azure.com/api"

def _login(team_id, password):
    """Login to get authentication token"""
    response = requests.post(
        f"{CPU_API_URL}/auth/login",
        json={"name": team_id, "password": password}
    )
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")
    return response.json()["access_token"]


def challenge1(folder_path, team_id, password):
    """
    Submit Task 1 (Image Reconstruction) for evaluation
    
    Args:
        folder_path: Path to folder containing part1_*.pt files
        team_id: Your team name/ID
        password: Your team password
    
    Returns:
        dict: Submission result with score
    """
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
        raise ValueError(f"Missing required files:\n{missing}")

    print("✅ All filenames validated")

    # ---------- Shape check ----------
    print("Validating tensor dimensions...")
    for idx in tqdm(sorted(matched_files), desc="Checking shapes"):
        f = matched_files[idx]
        path = os.path.join(folder_path, f)
        try:
            t = torch.load(path, map_location='cpu')
            if t.shape != (29, 96, 96):
                raise ValueError(f"{f}: invalid shape {t.shape}, expected (29, 96, 96)")
        except Exception as e:
            raise ValueError(f"Failed to load/check {f}: {e}")

    print("✅ All tensors have correct shape")

    # ---------- Zip ----------
    zip_filename = f"{team_id}_task1.zip"

    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for idx in tqdm(sorted(matched_files), desc="Zipping"):
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
            self.pbar = tqdm(total=self.size, unit='B', unit_scale=True, unit_divisor=1024, desc="Uploading")
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
            files=files,
            timeout=600
        )
        wrapped_file.close()
    except Exception as e:
        if os.path.exists(zip_filename):
            os.remove(zip_filename)
        raise Exception(f"Upload failed: {e}")

    # ---------- Cleanup ----------
    if os.path.exists(zip_filename):
        os.remove(zip_filename)

    if resp.status_code == 200:
        data = resp.json()
        print(f"\n✅ Submission Successful!")
        print(f"📊 Score: {data['public_score']:.2f}")
        return data
    else:
        print(f"\n❌ Submission Failed: {resp.text}")
        return None


def challenge2(model_path, team_id, password, wait_for_result=True):
    """
    Submit Task 2 (ONNX Model) for evaluation on GPU server
    
    Args:
        model_path: Path to .onnx model file
        team_id: Your team name/ID
        password: Your team password
        wait_for_result: Whether to wait and poll for results (default: True)
    
    Returns:
        dict: Submission result with score (if wait_for_result=True)
    """
    print(f"Submitting Task 2 for team {team_id}...")
    
    # ---------- Validation ----------
    if not os.path.isfile(model_path):
        raise ValueError(f"Model file not found: {model_path}")
    
    if not model_path.endswith('.onnx'):
        raise ValueError("Invalid file type. Must be .onnx file")
    
    file_size_mb = os.path.getsize(model_path) / (1024 * 1024)
    print(f"📦 Model size: {file_size_mb:.2f} MB")
    
    if file_size_mb > 100:
        raise ValueError(f"Model too large: {file_size_mb:.1f}MB (max 100MB)")
    
    # ---------- Login ----------
    print("🔐 Authenticating...")
    try:
        token = _login(team_id, password)
    except Exception as e:
        raise Exception(f"Authentication failed: {e}")
    
    # ---------- Get GPU Server URL ----------
    try:
        response = requests.get(f"{CPU_API_URL}/gpu-server-ip", timeout=10)
        if response.status_code != 200:
            raise Exception(f"Failed to get GPU server IP: {response.text}")
        GPU_API_URL = response.json()["gpu_server_ip"]
    except Exception as e:
        raise Exception(f"Failed to locate GPU server: {e}")

    # ---------- Upload to GPU Server ----------
    print("⬆️  Uploading model to server...")

    class ProgressFileWrapper:
        def __init__(self, filepath, mode='rb'):
            self.filepath = filepath
            self.file = open(filepath, mode)
            self.size = os.path.getsize(filepath)
            self.pbar = tqdm(
                total=self.size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
                desc="Uploading"
            )
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
        resp = requests.post(
            f"{GPU_API_URL}/submit/task2",
            files=files,
            data={'team_token': token},
            timeout=60
        )
        wrapped_file.close()
    except Exception as e:
        raise Exception(f"Upload failed: {e}")
    
    # ---------- Handle Response ----------
    if resp.status_code != 202:
        print(f"\n❌ Submission Failed: {resp.text}")
        return None
    
    result = resp.json()
    submission_id = result['submission_id']
    queue_position = result.get('queue_position', 0)
    
    print(f"\n✅ Submission Queued Successfully!")
    print(f"🆔 Submission ID: {submission_id}")
    print(f"📊 Queue Position: {queue_position}")
    
    # ---------- Wait for Results or Exit ----------
    if not wait_for_result:
        print("\n💡 Check your results later on the leaderboard!")
        return result
    
    # Smart waiting logic based on queue position
    if queue_position > 3:
        print(f"\n⏳ Queue position is {queue_position} (>3)")
        print("💡 You can safely close this notebook and check the leaderboard later.")
        print("   Or press Ctrl+C to stop waiting and check results manually.")
        print("\n⏱️  Waiting for results...")
    else:
        print(f"\n⏱️  Queue position is {queue_position} - waiting for results...")
    
    # ---------- Poll for Results ----------
    return _poll_for_results(GPU_API_URL, submission_id, team_id)


def _poll_for_results(gpu_url, submission_id, team_id, max_wait_minutes=15):
    """
    Poll GPU server for evaluation results
    
    Args:
        gpu_url: GPU server base URL
        submission_id: Submission ID to check
        team_id: Team ID for display
        max_wait_minutes: Maximum time to wait (default: 15 minutes)
    
    Returns:
        dict: Final result with score
    """
    max_attempts = max_wait_minutes * 60  # 1 attempt per second
    attempt = 0
    last_status = None
    
    try:
        with tqdm(total=100, desc="Processing", unit="%", bar_format='{l_bar}{bar}| {elapsed}') as pbar:
            while attempt < max_attempts:
                try:
                    response = requests.get(
                        f"{gpu_url}/submit/task2/status/{submission_id}",
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        status = data.get('status', 'processing')
                        
                        # Update progress bar on status change
                        if status != last_status:
                            if status == 'queued':
                                pbar.n = 10
                            elif status == 'processing':
                                pbar.n = 50
                            elif status == 'completed':
                                pbar.n = 100
                            pbar.refresh()
                            last_status = status
                        
                        if status == 'completed':
                            score = data.get('score', 0)
                            details = data.get('details', {})
                            
                            print(f"\n\n🎉 Evaluation Complete!")
                            print(f"📊 Final Score: {score:.2f}")
                            print(f"\n📈 Details:")
                            print(f"   • Inference Time: {details.get('inference_time', 0):.4f}s")
                            print(f"   • Throughput: {details.get('throughput_samples_per_sec', 0):.2f} samples/sec")
                            print(f"   • Model Size: {details.get('model_size_mb', 0):.2f} MB")
                            
                            # Get leaderboard position
                            try:
                                lb_response = requests.get(f"{CPU_API_URL}/leaderboard/task2?team_name={team_id}")
                                if lb_response.status_code == 200:
                                    leaderboard = lb_response.json()
                                    for entry in leaderboard:
                                        if entry['team_name'] == team_id:
                                            print(f"\n🏆 Your Rank: #{entry['rank']}")
                                            break
                            except:
                                pass
                            
                            print(f"\n✅ View full leaderboard at: {CPU_API_URL.replace('/api', '')}/")
                            return data
                        
                        elif status == 'failed':
                            error = data.get('error', 'Unknown error')
                            print(f"\n\n❌ Evaluation Failed!")
                            print(f"Error: {error}")
                            return data
                        
                        # Still processing
                        queue_length = data.get('queue_length', 0)
                        if queue_length > 0 and attempt % 10 == 0:
                            print(f"\r⏳ Queue length: {queue_length}     ", end='', flush=True)
                    
                    elif response.status_code == 202:
                        # Still in queue/processing
                        pass
                    
                except requests.exceptions.RequestException:
                    # Network error, continue polling
                    pass
                
                time.sleep(1)
                attempt += 1
            
            # Timeout
            print(f"\n\n⏱️  Polling timeout after {max_wait_minutes} minutes")
            print(f"💡 Your submission is still processing. Check the leaderboard later:")
            print(f"   {CPU_API_URL.replace('/api', '')}/")
            return {'status': 'timeout', 'submission_id': submission_id}
    
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Polling interrupted by user")
        print(f"💡 Your submission is still processing. Check the leaderboard later:")
        print(f"   {CPU_API_URL.replace('/api', '')}/")
        print(f"   Or check status with submission ID: {submission_id}")
        return {'status': 'interrupted', 'submission_id': submission_id}


def get_submission_status(submission_id, team_id=None, password=None):
    """
    Manually check the status of a Task 2 submission
    
    Args:
        submission_id: The submission ID to check
        team_id: Optional team ID (for login if needed)
        password: Optional password (for login if needed)
    
    Returns:
        dict: Current submission status
    """
    try:
        # Get GPU server URL
        response = requests.get(f"{CPU_API_URL}/gpu-server-ip", timeout=10)
        if response.status_code != 200:
            raise Exception("Failed to get GPU server IP")
        GPU_API_URL = response.json()["gpu_server_ip"]
        
        # Check status
        response = requests.get(
            f"{GPU_API_URL}/submit/task2/status/{submission_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'unknown')
            
            print(f"Status: {status}")
            
            if status == 'completed':
                print(f"Score: {data.get('score', 0):.2f}")
                print(f"Details: {data.get('details', {})}")
            elif status == 'failed':
                print(f"Error: {data.get('error', 'Unknown error')}")
            elif status == 'processing':
                print(f"Queue length: {data.get('queue_length', 0)}")
            
            return data
        else:
            print(f"Failed to get status: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error checking status: {e}")
        return None


# Helper function for quick testing
def test_submission(model_path, team_id, password):
    """Quick test submission without waiting"""
    return challenge2(model_path, team_id, password, wait_for_result=False)