import os
import time
import subprocess
import requests
import torch
import shutil
# import GOAT # Will import dynamically or ensure path is set
import sys

# Ensure we can import GOAT
sys.path.append(os.getcwd())
from GOAT import submit, leaderboard

API_URL = "http://localhost:8000"

def setup_test_data():
    print("Generating Test Data...")
    
    # 1. Ground Truth for Task 1 (Needed on Server)
    gt_dir = r"C:\Users\chate\Desktop\MLS-GOAT\data\gt_task1"
    os.makedirs(gt_dir, exist_ok=True)
    
    # Create 5 random tensors
    for i in range(5):
        t = torch.rand(29, 96, 96)
        torch.save(t, os.path.join(gt_dir, f"img_{i}.pt"))
        
    # 2. Submission Data for Task 1
    sub_task1_dir = "test_task1"
    if os.path.exists(sub_task1_dir):
        shutil.rmtree(sub_task1_dir)
    os.makedirs(sub_task1_dir)
    
    # Create matching tensors (slightly perturbed for psnr < inf)
    for i in range(5):
        # GT loaded
        gt = torch.load(os.path.join(gt_dir, f"img_{i}.pt"))
        # Add noise
        noise = torch.randn(29, 96, 96) * 0.01
        pred = gt + noise
        torch.save(pred, os.path.join(sub_task1_dir, f"img_{i}.pt"))
        
    print(f"Created {sub_task1_dir} with 5 tensor files.")

    # 3. Submission Data for Task 2
    # Just a dummy file named .onnx
    with open("test_model.onnx", "wb") as f:
        f.write(os.urandom(1024 * 1024 * 5)) # 5MB dummy file
        
    print("Created test_model.onnx")

def run_tests():
    # 1. Login/Check Admin (Assuming server running and admin created)
    # We will use the 'admin' created by create_initial_admin.py
    
    print("\n--- Testing Task 1 Submission ---")
    try:
        res = submit.challenge1('test_task1', 'admin', 'admin')
        if res:
            print("Task 1 Result:", res)
    except Exception as e:
        print("Task 1 Failed:", e)
        
    print("\n--- Testing Task 2 Submission ---")
    try:
        res = submit.challenge2('test_model.onnx', 'admin', 'admin')
        if res:
             print("Task 2 Result:", res)
    except Exception as e:
         print("Task 2 Failed:", e)
         
    print("\n--- Testing Leaderboard ---")
    leaderboard.getLB_chall1('admin')
    leaderboard.getLB_chall2('admin')

if __name__ == "__main__":
    setup_test_data()
    
    # We assume the user has started the backend or we can try to hit it.
    try:
        requests.get(API_URL)
        print("Backend is accessible.")
        run_tests()
    except:
        print("Backend not running. Please run 'uvicorn backend.main:app --reload' in a separate terminal.")
