import os
import torch
import torch.nn.functional as F
import time
import json
from tqdm import tqdm
import math
from pathlib import Path

class Scorer:
    def __init__(self, ground_truth_dir_task1=None):
        self.gt_dir_task1 = ground_truth_dir_task1

    def calc_psnr(self, pred, gt, eps=1e-8):
        mse = F.mse_loss(pred, gt)
        if mse < eps:
            return 50.0
        return (10.0 * torch.log10(1.0 / (mse + eps))).item()

    def calc_ssim(self, pred, gt, window_size=7):
        C1, C2 = 0.01**2, 0.03**2
        pad = window_size // 2
        mu_p = F.avg_pool2d(pred, window_size, 1, pad)
        mu_g = F.avg_pool2d(gt, window_size, 1, pad)
        sigma_p_sq = F.avg_pool2d(pred ** 2, window_size, 1, pad) - mu_p ** 2
        sigma_g_sq = F.avg_pool2d(gt ** 2, window_size, 1, pad) - mu_g ** 2
        sigma_pg = F.avg_pool2d(pred * gt, window_size, 1, pad) - mu_p * mu_g
        sigma_p_sq = torch.clamp(sigma_p_sq, min=0)
        sigma_g_sq = torch.clamp(sigma_g_sq, min=0)
        ssim = ((2 * mu_p * mu_g + C1) * (2 * sigma_pg + C2)) / (
            (mu_p ** 2 + mu_g ** 2 + C1) * (sigma_p_sq + sigma_g_sq + C2) + 1e-8
        )
        return ssim.mean().item()

    def calc_sam(self, pred, gt, eps=1e-8):
        B, C, H, W = pred.shape
        p = pred.reshape(B, C, -1)
        g = gt.reshape(B, C, -1)
        dot = (p * g).sum(dim=1)
        p_norm = torch.sqrt((p ** 2).sum(dim=1) + eps)
        g_norm = torch.sqrt((g ** 2).sum(dim=1) + eps)
        cos_sim = torch.clamp(dot / (p_norm * g_norm + eps), -1.0 + eps, 1.0 - eps)
        sam_deg = (torch.acos(cos_sim) * 180.0 / math.pi).mean()
        return sam_deg.item()

    def aggregate_score(self, psnr, ssim, sam):
        out = (0.5*psnr / 50 + 0.25*ssim + 0.25*(1 - sam / 90))
        return 1.0 if out >= 0.999 else out

    def evaluate_task1(self, pred_dir, public=True):
        """
        Evaluates Task 1: PSNR, SSIM, and SAM metrics
        pred_dir: Directory containing participant's .pt files
        public: If True, evaluate on sample_0000.pt to sample_0059.pt (60 files)
                If False, evaluate on sample_0000.pt to sample_0299.pt (300 files)
        """
        if not self.gt_dir_task1:
            raise ValueError("Ground Truth directory for Task 1 not set")

        print(f"Evaluating Task 1 ({'public' if public else 'private'})... Pred: {pred_dir}, GT: {self.gt_dir_task1}")
        
        # Define file range based on public/private
        if public:
            file_range = range(60)  # sample_0000.pt to sample_0059.pt
        else:
            file_range = range(300)  # sample_0000.pt to sample_0299.pt
        
        gt_files = []
        pred_files = []
        
        for i in file_range:
            filename = f"sample_{i:04d}.pt"
            gt_path = Path(self.gt_dir_task1) / filename
            pred_path = Path(pred_dir) / filename
            
            if gt_path.exists() and pred_path.exists():
                gt_files.append(gt_path)
                pred_files.append(pred_path)
        
        if len(gt_files) == 0 or len(pred_files) == 0:
            return 0.0, {"error": "No matching .pt files found"}
        
        if len(gt_files) != len(pred_files):
            return 0.0, {"error": f"File count mismatch: {len(gt_files)} GT vs {len(pred_files)} pred"}

        total_psnr, total_ssim, total_sam = 0.0, 0.0, 0.0
        n = len(gt_files)
        
        try:
            for gf, pf in zip(gt_files, pred_files):
                gt = torch.load(gf, weights_only=True).float().unsqueeze(0)
                pred = torch.load(pf, weights_only=True).float().unsqueeze(0)

                total_psnr += self.calc_psnr(pred, gt)
                total_ssim += self.calc_ssim(pred, gt)
                total_sam += self.calc_sam(pred, gt)

            avg_psnr = total_psnr / n
            avg_ssim = total_ssim / n
            avg_sam = total_sam / n
            
            final_score = self.aggregate_score(avg_psnr, avg_ssim, avg_sam)
            
            return final_score, {
                "score": final_score,
                "average_psnr": avg_psnr,
                "average_ssim": avg_ssim,
                "average_sam": avg_sam,
                "files_evaluated": n
            }
        except Exception as e:
            print(f"Error during evaluation: {e}")
            return 0.0, {"error": str(e)}
        
scorer = Scorer()
# You must set scorer.gt_dir_task1 before calling evaluate_task1
