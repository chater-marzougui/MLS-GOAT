"""Scoring calculations for model evaluation"""

import numpy as np
import logging

logger = logging.getLogger(__name__)


def calculate_rmse(predictions, ground_truth):
    """Calculate Root Mean Square Error between predictions and ground truth"""
    # Ensure same shape
    if predictions.shape != ground_truth.shape:
        logger.warning(f"Shape mismatch - predictions: {predictions.shape}, ground_truth: {ground_truth.shape}")
        # If predictions have channel dimension but ground truth doesn't, squeeze it
        if len(predictions.shape) == 4 and predictions.shape[1] == 1:
            predictions = predictions.squeeze(1)
        elif len(predictions.shape) == 3 and predictions.shape[0] == 1:
            predictions = predictions.squeeze(0)
    
    # Normalize both to same range if needed
    if predictions.max() > 1.0 and ground_truth.max() <= 1.0:
        predictions = predictions / 255.0
    elif predictions.max() <= 1.0 and ground_truth.max() > 1.0:
        ground_truth = ground_truth / 255.0
    
    mse = np.mean((predictions - ground_truth) ** 2)
    rmse = np.sqrt(mse)
    
    return float(rmse)


def calculate_score(results):
    """Calculate final score based on accuracy, model size, and inference time"""
    # Score formula: accuracy_score * size_score * speed_score
    # where:
    #   accuracy_score = 1/(1+rmse)
    #   size_score = (50 - model_size_mb) / 20
    #   speed_score = 0.16 + log2(7 + inference_time)
    
    accuracy_score = results['accuracy_score']  # Already calculated as 1/(1+rmse)
    model_size_mb = results['model_size_mb']
    inference_time = results['inference_time']
    
    # Model size score: (50 - model_size) / 20
    # Penalizes models larger than 50MB
    size_score = (50.0 - model_size_mb) / 20.0
    
    # Inference time score: 0.16 + log10(7 + inference_time)
    speed_score = 0.16 + np.log10(7.0 - (2/5.33) * inference_time)
    
    # Final score is the product of all three
    total_score = accuracy_score * size_score * speed_score
    
    logger.info(f"Score breakdown - Accuracy: {accuracy_score:.6f}, Size: {size_score:.6f}, Speed: {speed_score:.6f}, Total: {total_score:.6f}")
    
    return total_score
