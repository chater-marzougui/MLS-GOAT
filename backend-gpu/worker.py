import os
import sys
import time
import json
import redis
import numpy as np
import onnxruntime as ort
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=f'[Worker-{os.getenv("WORKER_ID", "0")}] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
WORKER_ID = os.getenv('WORKER_ID', '0')
GPU_MEMORY_FRACTION = float(os.getenv('GPU_MEMORY_FRACTION', 0.143))

# Connect to Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

def configure_onnx_gpu():
    """Configure ONNX Runtime to use limited GPU memory"""
    providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
    
    provider_options = [{
        'device_id': 0,
        'gpu_mem_limit': int(GPU_MEMORY_FRACTION * 46 * 1024 * 1024 * 1024),  # Convert to bytes
        'arena_extend_strategy': 'kSameAsRequested',
    }]
    
    return providers, provider_options

def load_test_data(test_data_path):
    """Load test dataset for evaluation"""
    # Adjust this based on your actual test data format
    # Example: load from numpy files, images, etc.
    try:
        # Replace with your actual test data loading logic
        test_data = np.load(test_data_path, allow_pickle=True)
        logger.info(f"Loaded test data with shape: {test_data.shape if hasattr(test_data, 'shape') else 'N/A'}")
        return test_data
    except Exception as e:
        logger.error(f"Failed to load test data: {e}")
        raise

def evaluate_model(model_path, test_data_path):
    """Evaluate ONNX model on test dataset"""
    try:
        start_time = time.time()
        
        # Configure ONNX Runtime
        providers, provider_options = configure_onnx_gpu()
        
        logger.info(f"Loading model: {model_path}")
        session = ort.InferenceSession(
            model_path,
            providers=providers,
            provider_options=provider_options
        )
        
        # Get input/output names
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        
        logger.info(f"Model loaded. Input: {input_name}, Output: {output_name}")
        
        # Load test data
        test_data = load_test_data(test_data_path)
        
        # Run inference
        logger.info("Running inference...")
        predictions = []
        ground_truth = []
        
        # Adjust batching based on your data format
        batch_size = 32
        num_samples = len(test_data) if hasattr(test_data, '__len__') else test_data.shape[0]
        
        for i in range(0, num_samples, batch_size):
            batch = test_data[i:i+batch_size]
            
            # Preprocess batch if needed
            # batch = preprocess(batch)
            
            outputs = session.run([output_name], {input_name: batch})
            predictions.extend(outputs[0])
            
            # Extract ground truth if available
            # ground_truth.extend(batch_labels)
        
        # Calculate metrics
        inference_time = time.time() - start_time
        
        # Example metrics - adjust based on your task
        accuracy = calculate_accuracy(predictions, ground_truth) if ground_truth else 0.0
        
        # Calculate model size
        model_size_mb = os.path.getsize(model_path) / (1024 * 1024)
        
        results = {
            'accuracy': accuracy,
            'inference_time': inference_time,
            'model_size_mb': model_size_mb,
            'num_samples': num_samples,
            'avg_time_per_sample': inference_time / num_samples if num_samples > 0 else 0,
        }
        
        logger.info(f"Evaluation complete: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        raise

def calculate_accuracy(predictions, ground_truth):
    """Calculate accuracy metric - adjust based on your task"""
    if not ground_truth:
        return 0.0
    
    # Example for classification
    predictions = np.array(predictions)
    ground_truth = np.array(ground_truth)
    
    if len(predictions.shape) > 1:
        predictions = np.argmax(predictions, axis=1)
    
    accuracy = np.mean(predictions == ground_truth)
    return float(accuracy)

def calculate_score(results):
    """Calculate final score based on multiple metrics"""
    # Adjust scoring formula based on your requirements
    # Example: balance accuracy and efficiency
    
    accuracy = results['accuracy']
    model_size_mb = results['model_size_mb']
    inference_time = results['inference_time']
    
    # Example scoring: prioritize accuracy, penalize large models and slow inference
    # Adjust weights as needed
    score = (
        accuracy * 100 * 0.7 +  # 70% weight on accuracy
        (40 - model_size_mb) * 0.15 +  # 15% weight on model size (smaller is better)
        (10 / max(inference_time, 0.1)) * 0.15  # 15% weight on speed
    )
    
    return max(0, min(100, score))  # Clamp between 0-100

def process_job(job_data):
    """Process a single evaluation job"""
    try:
        submission_id = job_data['submission_id']
        model_path = job_data['model_path']
        test_data_path = job_data['test_data_path']
        
        logger.info(f"Processing submission {submission_id}")
        
        # Evaluate model
        results = evaluate_model(model_path, test_data_path)
        
        # Calculate final score
        score = calculate_score(results)
        
        # Store results
        result = {
            'submission_id': submission_id,
            'worker_id': WORKER_ID,
            'score': score,
            'details': results,
            'status': 'completed',
            'timestamp': time.time()
        }
        
        # Save to Redis results
        redis_client.hset(
            f'result:{submission_id}',
            mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in result.items()}
        )
        redis_client.expire(f'result:{submission_id}', 3600)  # Expire after 1 hour
        
        logger.info(f"Submission {submission_id} completed with score: {score:.2f}")
        return result
        
    except Exception as e:
        logger.error(f"Job processing failed: {e}", exc_info=True)
        
        # Store error result
        error_result = {
            'submission_id': job_data.get('submission_id', 'unknown'),
            'worker_id': WORKER_ID,
            'status': 'failed',
            'error': str(e),
            'timestamp': time.time()
        }
        
        redis_client.hset(
            f'result:{job_data.get("submission_id", "unknown")}',
            mapping={k: str(v) for k, v in error_result.items()}
        )
        
        return error_result

def main():
    """Main worker loop"""
    logger.info(f"Worker {WORKER_ID} starting...")
    logger.info(f"GPU Memory Fraction: {GPU_MEMORY_FRACTION}")
    logger.info(f"Redis Host: {REDIS_HOST}")
    
    # Test Redis connection
    try:
        redis_client.ping()
        logger.info("Redis connection successful")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        sys.exit(1)
    
    # Worker loop
    while True:
        try:
            # Block and wait for job (BRPOP with timeout)
            result = redis_client.brpop('evaluation_queue', timeout=5)
            
            if result:
                queue_name, job_json = result
                job_data = json.loads(job_json)
                
                logger.info(f"Received job: {job_data.get('submission_id', 'unknown')}")
                
                # Process the job
                process_job(job_data)
                
            else:
                # No job available, just wait
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Worker shutting down...")
            break
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            time.sleep(5)  # Wait before retrying

if __name__ == '__main__':
    main()
