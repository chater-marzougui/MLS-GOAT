import os
import torch
import time
import json
from tqdm import tqdm
import math

class Scorer:
    def __init__(self, ground_truth_dir_task1=None):
        self.gt_dir_task1 = ground_truth_dir_task1

    def calculate_psnr_single(self, pred, target, max_val=1.0, cap=100.0):
        mse = torch.mean((pred - target) ** 2)
        psnr = 20 * torch.log10(torch.tensor(max_val)) - 10 * torch.log10(mse + 1e-10)
        return min(psnr.item(), cap)

    def evaluate_task1(self, pred_dir):
        """
        Evaluates Task 1: PSNR Check
        pred_dir: Directory containing participant's .pt files
        gt_dir: Directory containing ground truth .pt files
        """
        if not self.gt_dir_task1:
            raise ValueError("Ground Truth directory for Task 1 not set")

        print(f"Evaluating Task 1... Pred: {pred_dir}, GT: {self.gt_dir_task1}")
        
        pred_files = set(f for f in os.listdir(pred_dir) if f.endswith('.pt'))
        gt_files = set(f for f in os.listdir(self.gt_dir_task1) if f.endswith('.pt'))
        
        common_files = sorted(pred_files & gt_files)
        
        if len(common_files) == 0:
            return 0.0, {"error": "No matching .pt files found"}

        all_psnr = []
        # Check for GPU
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        for f in common_files:
            try:
                pred_path = os.path.join(pred_dir, f)
                gt_path = os.path.join(self.gt_dir_task1, f)
                
                pred = torch.load(pred_path, map_location=device).float()
                gt = torch.load(gt_path, map_location=device).float()
                
                psnr_val = self.calculate_psnr_single(pred.cpu(), gt.cpu()) # Calc on CPU to be safe or keep on device? CPU is fine for scalar calc usually
                all_psnr.append(psnr_val)
            except Exception as e:
                print(f"Error processing {f}: {e}")
                
        if not all_psnr:
             return 0.0, {"error": "Failed to process files"}

        avg_psnr = sum(all_psnr) / len(all_psnr)
        
        return avg_psnr, {
            "average_psnr": avg_psnr,
            "min_psnr": min(all_psnr),
            "max_psnr": max(all_psnr),
            "files_evaluated": len(common_files)
        }

    def evaluate_task2(self, model_path):
        """
        Evaluates Task 2: ONNX Model
        - Size
        - Inference Time
        - Accuracy (Placeholder 100%)
        """
        # 1. Model Size
        size_bytes = os.path.getsize(model_path)
        size_mb = size_bytes / (1024 * 1024)
        
        # Scoring constraints from prompt:
        # 0MB = Perfect, 180MB = 0 Score. 
        # Linear interpolation? Or just raw values? Prompt says "weighted score".
        # Let's normalize to 0-1 scale first.
        # Size Score: 1.0 if size -> 0, 0.0 if size >= 180
        size_score = max(0, (180 - size_mb) / 180)

        # 2. Inference Time
        # Load model to warm up
        # We need a dummy input. Since I don't know the input shape, I might need to inspect the model.
        # For now, I will Mock inference time as requested or try to run if input shape known.
        # User said "calculate accuracy while giving weighted score based on accuracy, model size, inference time"
        # and "100% accuracy as placeholder".
        # I'll just measure load time + a dummy run if possible, or purely mock the time part if I can't determine input shape.
        # But wait, user: "submit same image we just need to verify size works the rest make random time"
        
        import random
        inference_time = random.uniform(0.1, 10.0) # Mock
        
        # Time Score: 0s = Perfect, 10s = 0 Score
        time_score = max(0, (10 - inference_time) / 10)
        
        # 3. Accuracy
        accuracy = 1.0 # Placeholder
        
        # Weighted Score
        # Weights: Acc=0.5, Size=0.25, Time=0.25 (My proposal, User didn't object)
        final_score = (accuracy * 0.5) + (size_score * 0.25) + (time_score * 0.25)
        
        # Scale to 100? Or keep 0-1? Prompt used dB for Task 1 (0-100). Let's do 0-100 for Task 2 as well.
        final_score *= 100
        
        return final_score, {
            "accuracy": accuracy,
            "size_mb": size_mb,
            "inference_time_s": inference_time,
            "size_score": size_score,
            "time_score": time_score,
            "final_score": final_score
        }

scorer = Scorer()
# You must set scorer.gt_dir_task1 before calling evaluate_task1
