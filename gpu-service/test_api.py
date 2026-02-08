#!/usr/bin/env python3
"""Test script for the full API with file upload"""

import requests
import time
import sys
from pathlib import Path

API_URL = "http://localhost:8000"
MODEL_PATH = "backend/data/uploads/sub_1770525983_1b411471.onnx"


def _login(team_id, password):
    """Login to get authentication token"""
    response = requests.post(
        f"https://mls-goat.eastus2.cloudapp.azure.com/api/auth/login",
        json={"name": team_id, "password": password}
    )
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")
    return response.json()["access_token"]

TEAM_TOKEN = _login("Rizz team", r"SmNzn7gboTwKY33o")
BATCH_SIZE = 8

def test_health():
    """Test health endpoint"""
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"   ✓ Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

def test_submit_health():
    """Test submit health endpoint"""
    print("\n2. Testing submit health endpoint...")
    try:
        response = requests.get(f"{API_URL}/submit/health")
        print(f"   ✓ Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

def test_model_submission():
    """Test model submission"""
    print("\n3. Submitting model for evaluation...")
    
    model_path = Path(MODEL_PATH)
    if not model_path.exists():
        print(f"   ✗ Model file not found: {MODEL_PATH}")
        return None
    
    try:
        with open(model_path, 'rb') as f:
            files = {'file': (model_path.name, f, 'application/octet-stream')}
            data = {
                'team_token': TEAM_TOKEN,
                'is_private': True,
                'batch_size': BATCH_SIZE
            }
            response = requests.post(f"{API_URL}/submit/task2", files=files, data=data)
        
        print(f"   ✓ Status: {response.status_code}")
        result = response.json()
        print(f"   Response: {result}")
        
        if response.status_code == 202:
            submission_id = result.get('submission_id')
            print(f"   ✓ Submission ID: {submission_id}")
            return submission_id
        else:
            print(f"   ✗ Unexpected status code")
            print(f"   Error: {result.get('detail', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return None

def test_check_status(submission_id):
    """Test status checking"""
    print(f"\n4. Checking submission status...")
    
    max_wait = 180  # 3 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{API_URL}/submit/task2/status/{submission_id}")
            result = response.json()
            
            status = result.get('status', 'unknown')
            print(f"   Status: {status}", end='')
            
            if status == 'completed':
                print(f"\n   ✓ Evaluation complete!")
                print(f"   Score: {result.get('score', 'N/A')}")
                print(f"   Worker: {result.get('worker_id', 'N/A')}")
                if 'details' in result:
                    print(f"   Details: {result['details']}")
                return True
            elif status == 'failed':
                print(f"\n   ✗ Evaluation failed")
                print(f"   Error: {result.get('error', 'Unknown error')}")
                return False
            else:
                elapsed = int(time.time() - start_time)
                print(f" (waiting... {elapsed}s)", end='\r')
                time.sleep(3)
                
        except Exception as e:
            print(f"\n   ✗ Status check failed: {e}")
            return False
    
    print(f"\n   ✗ Timeout after {max_wait}s")
    return False

def test_queue_status():
    """Test queue status"""
    print("\n5. Checking queue status...")
    try:
        response = requests.get(f"{API_URL}/submit/queue/status")
        print(f"   ✓ Status: {response.status_code}")
        result = response.json()
        print(f"   Queue length: {result.get('queue_length', 'N/A')}")
        print(f"   Total workers: {result.get('total_workers', 'N/A')}")
        print(f"   Recent results: {result.get('recent_results_count', 'N/A')}")
        return True
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

def main():
    print("="*60)
    print("Full API Test with File Upload")
    print("="*60)
    print(f"Model: {MODEL_PATH}")
    print(f"Batch Size: {BATCH_SIZE}")
    print(f"Team Token: {TEAM_TOKEN[:20]}..." if len(TEAM_TOKEN) > 20 else f"Team Token: {TEAM_TOKEN}")
    print("="*60)
    
    # Test health endpoints
    if not test_health():
        print("\n✗ Backend not responding. Is it running?")
        print("  Start with: sudo docker compose up -d")
        sys.exit(1)
    
    test_submit_health()
    
    # Test queue status
    test_queue_status()
    
    # Submit model
    submission_id = test_model_submission()
    if not submission_id:
        print("\n✗ Model submission failed")
        sys.exit(1)
    
    # Check status until complete
    success = test_check_status(submission_id)
    
    # Final queue status
    test_queue_status()
    
    print("\n" + "="*60)
    if success:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("="*60)

if __name__ == '__main__':
    main()
