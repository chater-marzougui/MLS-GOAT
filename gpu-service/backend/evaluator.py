"""Model evaluation and inference"""

import time
import os
import json
import numpy as np
import onnxruntime as ort
import logging

from data_loader import load_test_data, load_ground_truth
from scorer import calculate_rmse

logger = logging.getLogger(__name__)


def configure_onnx_gpu(gpu_memory_fraction):
    """Configure ONNX Runtime to use limited GPU memory with optimizations"""
    # Session options for optimal performance
    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    
    providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
    
    provider_options = [
        {
            'device_id': 0,
            'gpu_mem_limit': int(gpu_memory_fraction * 46 * 1024 * 1024 * 1024),
            'arena_extend_strategy': 'kSameAsRequested',
        },
        {}  # Empty dict for CPUExecutionProvider
    ]
    
    return providers, provider_options, sess_options

def normalize(x):
    """Normalize predictions to [0, 1] range for each sample in batch"""
    # Reshape to (batch_size, -1) to find min/max per sample
    batch_size = x.shape[0]
    x_flat = x.reshape(batch_size, -1)
    
    # Find min and max per sample
    x_min = x_flat.min(axis=1, keepdims=True)
    x_max = x_flat.max(axis=1, keepdims=True)
    
    # Normalize
    x_flat_normalized = (x_flat - x_min) / (x_max - x_min + 1e-8)
    
    # Reshape back to original shape
    return x_flat_normalized.reshape(x.shape)

def run_inference_batch(session, input_name, output_name, test_data, batch_size=8):
    """Run inference on test data with precise timing"""
    num_samples = len(test_data) if hasattr(test_data, '__len__') else test_data.shape[0]
    predictions = []
    
    inference_start = time.perf_counter()
    
    for i in range(0, num_samples, batch_size):
        batch = test_data[i:i+batch_size]
        outputs = session.run([output_name], {input_name: batch})
        normalized_outputs = normalize(outputs[0])
        predictions.append(normalized_outputs)
    
    inference_time = time.perf_counter() - inference_start
    
    predictions = np.concatenate(predictions, axis=0)
    return predictions, inference_time, num_samples


def evaluate_model(model_path, test_data_path, batch_size, gpu_memory_fraction):
    """Evaluate ONNX model on test dataset with warmup and multiple runs"""
    try:
        # Configure ONNX Runtime
        providers, provider_options, sess_options = configure_onnx_gpu(gpu_memory_fraction)
        
        logger.info(f"Loading model: {model_path}")
        model_load_start = time.perf_counter()
        session = ort.InferenceSession(
            model_path,
            sess_options=sess_options,
            providers=providers,
            provider_options=provider_options
        )
        model_load_time = time.perf_counter() - model_load_start
        logger.info(f"Model loaded in {model_load_time:.2f}s")
        
        # Get input/output names
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        
        logger.info(f"Input: {input_name}, Output: {output_name}")
        
        # Load test data (cached after first load)
        data_load_start = time.perf_counter()
        test_data, sample_names = load_test_data(test_data_path)
        ground_truth = load_ground_truth(test_data_path, sample_names)
        data_load_time = time.perf_counter() - data_load_start
        logger.info(f"Test data and ground truth loaded in {data_load_time:.2f}s")
        
        logger.info(f"Using batch size: {batch_size}")
        
        # WARMUP RUN - not counted in scoring
        logger.info("Running warmup inference...")
        warmup_start = time.perf_counter()
        predictions, warm_time, _ = run_inference_batch(session, input_name, output_name, test_data, batch_size)
        warmup_time = time.perf_counter() - warmup_start
        logger.info(f"Warmup completed in {warmup_time:.2f}s")
        
        if warm_time > 513.0:
            error_msg = f"Warmup inference time {warm_time:.2f}s exceeds 13s limit for warmup run"
            logger.error(error_msg)
            raise ValueError(error_msg)
        # FIVE MEASURED RUNS - average these for scoring
        logger.info("Running 5 measured inference passes...")
        inference_times = []
        
        for run_num in range(5):
            logger.info(f"Running inference pass {run_num + 1}/5...")
            _, inference_time, num_samples = run_inference_batch(
                session, input_name, output_name, test_data, batch_size
            )
            
            # Check inference time limit (10 seconds per run)
            if inference_time > 510.0:
                error_msg = f"Inference time {inference_time:.2f}s exceeds 10s limit on run {run_num + 1}/5"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            inference_times.append(inference_time)
            logger.info(f"Pass {run_num + 1} completed in {inference_time:.4f}s")
        
        # Calculate average inference time
        avg_inference_time = np.median(inference_times)
        std_inference_time = np.std(inference_times)
        
        logger.info(f"Average inference time: {avg_inference_time:.4f}s ± {std_inference_time:.4f}s")
        
        # Calculate RMSE accuracy
        rmse = calculate_rmse(predictions, ground_truth)
        accuracy_score = 4.0 / (4.0 + (10*rmse)**2)
        
        logger.info(f"RMSE: {rmse:.6f}, Accuracy Score: {accuracy_score:.6f}")
        
        # Calculate additional metrics
        mean_depth = float(np.mean(predictions))
        std_depth = float(np.std(predictions))
        
        # Calculate model size
        model_size_mb = os.path.getsize(model_path) / (1024 * 1024)
        
        results = {
            'rmse': rmse,
            'accuracy_score': accuracy_score,
            'mean_depth': mean_depth,
            'std_depth': std_depth,
            'inference_time': avg_inference_time,  # Average of 3 runs
            'inference_time_std': std_inference_time,
            'inference_times_all': inference_times,  # All 3 times for transparency
            'model_size_mb': model_size_mb,
            'num_samples': num_samples,
            'batch_size': batch_size,
            'avg_time_per_sample': avg_inference_time / num_samples if num_samples > 0 else 0,
            'throughput_samples_per_sec': num_samples / avg_inference_time if avg_inference_time > 0 else 0,
            'model_load_time': model_load_time,
            'data_load_time': data_load_time,
            'warmup_time': warmup_time,
        }
        
        logger.info(f"Evaluation complete: {json.dumps(results, indent=2)}")
        return results
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        raise
