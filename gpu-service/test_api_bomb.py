#!/usr/bin/env python3
"""Stress test: Submit models and analyze worker performance"""

import requests
import time
import sys
from pathlib import Path
import statistics

API_URL = "http://localhost:8000"
NUM_SUBMISSIONS = 10

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def submit_model(model_name, batch_size):
    """Submit a single model"""
    model_path = Path('onnx_var_batch_size/'+model_name)
    if not model_path.exists():
        print_error("Model doesn't exist: "+str(model_path))
        return None
    
    try:
        with open(model_path, 'rb') as f:
            files = {'file': (model_name, f, 'application/octet-stream')}
            data = {'batch_size': batch_size}
            response = requests.post(f"{API_URL}/submit/task2", files=files, data=data)
        
        if response.status_code == 202:
            result = response.json()
            return result.get('submission_id')
        return None
    except Exception as e:
        print_error(f"Submission failed: {e}")
        return None

def check_status(submission_id):
    """Check status of a submission"""
    try:
        response = requests.get(f"{API_URL}/submit/task2/status/{submission_id}")
        return response.json()
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def full_test(model_name, batch_size):
    print_header(f"API STRESS TEST - {model_name} SUBMISSIONS (BATCH_SIZE={batch_size})")
    
    # Phase 1: Submit all models
    submissions = []
    submit_start = time.time()
    
    for i in range(NUM_SUBMISSIONS):
        submission_id = submit_model(model_name, batch_size)
        if submission_id:
            submissions.append({
                'id': submission_id,
                'submit_time': time.time(),
                'number': i + 1
            })
            print(f"  [{i+1}/{NUM_SUBMISSIONS}] Submitted: {submission_id}", end='\r')
        else:
            print_error(f"Failed to submit model #{i+1}")
    
    submit_duration = time.time() - submit_start
    print(f"\n")
    print_success(f"Submitted {len(submissions)} models in {submit_duration:.2f}s")
    print_info(f"Average submission rate: {len(submissions)/submit_duration:.2f} models/sec")
    
    # Phase 2: Wait for all completions
    print_header("WAITING FOR EVALUATIONS")
    
    completed = []
    failed = []
    max_wait = 600  # 10 minutes total
    start_wait = time.time()
    
    pending = submissions.copy()
    
    while pending and (time.time() - start_wait) < max_wait:
        for sub in pending[:]:
            result = check_status(sub['id'])
            status = result.get('status', 'unknown')
            
            if status == 'completed':
                sub['complete_time'] = time.time()
                sub['result'] = result
                sub['waiting_time'] = sub['complete_time'] - sub['submit_time']
                completed.append(sub)
                pending.remove(sub)
                
                score = result.get('score', 0)
                inference_time = result.get('details', {}).get('inference_time', 0)
                batch_size = result.get('details', {}).get('batch_size', batch_size)
                
                print_success(f"[{len(completed)}/{len(submissions)}] Model #{sub['number']} | "
                            f"Score: {score:.2f} | "
                            f"Inference: {inference_time:.2f}s | Wait: {sub['waiting_time']:.2f}s | BS: {batch_size}")
                
            elif status == 'failed':
                sub['result'] = result
                failed.append(sub)
                pending.remove(sub)
                print_error(f"Model #{sub['number']} failed: {result.get('error', 'Unknown')}")
        
        if pending:
            elapsed = int(time.time() - start_wait)
            print(f"  Waiting for {len(pending)} models... ({elapsed}s elapsed)", end='\r')
            time.sleep(2)
    
    # Phase 3: Analysis
    print_header("PERFORMANCE ANALYSIS")
    
    total_evaluated = len(completed)
    total_failed = len(failed)
    
    print(f"\n{Colors.BOLD}Overall Statistics:{Colors.ENDC}")
    print(f"  Total Submitted:  {len(submissions)}")
    print(f"  Completed:        {Colors.OKGREEN}{total_evaluated}{Colors.ENDC}")
    print(f"  Failed:           {Colors.FAIL}{total_failed}{Colors.ENDC}")
    print(f"  Still Pending:    {Colors.WARNING}{len(pending)}{Colors.ENDC}")
    
    if completed:
        # Timing statistics
        waiting_times = [s['waiting_time'] for s in completed]
        inference_times = [s['result'].get('details', {}).get('inference_time', 0) for s in completed]
        scores = [s['result'].get('score', 0) for s in completed]
        
        print(f"\n{Colors.BOLD}Timing Metrics:{Colors.ENDC}")
        print(f"  Average Waiting Time:    {statistics.mean(waiting_times):.2f}s")
        print(f"  Min Waiting Time:        {min(waiting_times):.2f}s")
        print(f"  Max Waiting Time:        {max(waiting_times):.2f}s")
        print(f"  Median Waiting Time:     {statistics.median(waiting_times):.2f}s")
        if len(waiting_times) > 1:
            print(f"  StdDev Waiting Time:     {statistics.stdev(waiting_times):.2f}s")
        
        print(f"\n{Colors.BOLD}Inference Performance:{Colors.ENDC}")
        print(f"  Average Inference Time:  {statistics.mean(inference_times):.2f}s")
        print(f"  Min Inference Time:      {min(inference_times):.2f}s")
        print(f"  Max Inference Time:      {max(inference_times):.2f}s")
        print(f"  Median Inference Time:   {statistics.median(inference_times):.2f}s")
        
        print(f"\n{Colors.BOLD}Score Statistics:{Colors.ENDC}")
        print(f"  Average Score:           {statistics.mean(scores):.4f}")
        print(f"  Min Score:               {min(scores):.4f}")
        print(f"  Max Score:               {max(scores):.4f}")
        print(f"  Score StdDev:            {statistics.stdev(scores) if len(scores) > 1 else 0:.4f}")
        
        # Throughput analysis
        total_time = time.time() - submit_start
        print(f"\n{Colors.BOLD}Throughput Analysis:{Colors.ENDC}")
        print(f"  Total Test Duration:     {total_time:.2f}s")
        print(f"  Overall Throughput:      {total_evaluated/total_time:.2f} models/sec")
        print(f"  Avg Time Per Model:      {total_time/total_evaluated:.2f}s")
        
        # Parallelization efficiency
        sequential_time = sum(inference_times)
        speedup = sequential_time / total_time if total_time > 0 else 0
        
        print(f"\n{Colors.BOLD}Sequential vs Parallel:{Colors.ENDC}")
        print(f"  Sequential Time (sum):   {sequential_time:.2f}s")
        print(f"  Parallel Time (actual):  {total_time:.2f}s")
        print(f"  Speedup:                 {speedup:.2f}x")
        
        # Queue behavior
        if total_evaluated >= 3:
            first_batch = sorted(completed, key=lambda x: x['complete_time'])[:min(3, total_evaluated)]
            avg_first_wait = statistics.mean([s['waiting_time'] for s in first_batch])
            
            last_batch = sorted(completed, key=lambda x: x['complete_time'])[-min(3, total_evaluated):]
            avg_last_wait = statistics.mean([s['waiting_time'] for s in last_batch])
            
            print(f"\n{Colors.BOLD}Queue Behavior:{Colors.ENDC}")
            print(f"  First {len(first_batch)} completions (avg wait):  {avg_first_wait:.2f}s")
            print(f"  Last {len(last_batch)} completions (avg wait):   {avg_last_wait:.2f}s")
            if avg_first_wait > 0:
                print(f"  Wait time change:                {avg_last_wait - avg_first_wait:.2f}s ({((avg_last_wait/avg_first_wait - 1)*100):.1f}%)")
    
    print_header("TEST COMPLETE")
    
    if total_evaluated == len(submissions):
        print_success(f"All {len(submissions)} models evaluated successfully!")
    elif total_evaluated > 0:
        print_info(f"Evaluated {total_evaluated}/{len(submissions)} models")
    else:
        print_error("No models were evaluated")


def main():
    
    # Check if backend is up
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code != 200:
            print_error("Backend not responding correctly")
            sys.exit(1)
    except:
        print_error("Backend not responding. Start with: sudo docker compose up -d")
        sys.exit(1)
    print_success(f"Backend is running")
    
    models_list = {
        'baseline_fp16_16.onnx': 16,
        'baseline_fp16_4.onnx': 4,
        'baseline_fp32_16.onnx': 16,
        'baseline_fp32_4.onnx': 4,
        'baseline_fp16_32.onnx': 32,
        'baseline_fp16_8.onnx': 8,
        'baseline_fp32_32.onnx': 32,
        'baseline_fp32_8.onnx': 8}
    for model_name, bs in models_list.items():
        full_test(model_name, bs)
        print('='*30)
        print('='*30)
        print('='*30)

if __name__ == '__main__':
    main()