"""Queue and job processing with Redis"""

import os
import json
import time
import redis
import requests
import logging

from evaluator import evaluate_model
from scorer import calculate_score

logger = logging.getLogger(__name__)


def get_redis_client(host, port):
    """Create and return Redis client"""
    return redis.Redis(host=host, port=port, db=0, decode_responses=True)


def get_team_best_score(redis_client, team_id):
    """Get the best score for a team from Redis"""
    try:
        best_score_key = f'team:{team_id}:best_score'
        best_score = redis_client.get(best_score_key)
        return float(best_score) if best_score else None
    except:
        return None


def update_team_best_model(redis_client, team_id, submission_id, score, model_path):
    """Update team's best model, delete old best if new one is better"""
    try:
        best_score_key = f'team:{team_id}:best_score'
        best_model_key = f'team:{team_id}:best_model'
        best_submission_key = f'team:{team_id}:best_submission'
        
        current_best_score = redis_client.get(best_score_key)
        current_best_model = redis_client.get(best_model_key)
        
        if current_best_score is None:
            # First submission for this team
            redis_client.set(best_score_key, score)
            redis_client.set(best_model_key, model_path)
            redis_client.set(best_submission_key, submission_id)
            logger.info(f"Team {team_id}: First submission, keeping model at {model_path}")
            return True  # Keep this model
        else:
            current_best_score = float(current_best_score)
            
            if score > current_best_score:
                # New model is better - delete old best, keep new
                
                # Update to new best
                redis_client.set(best_score_key, score)
                redis_client.set(best_model_key, model_path)
                redis_client.set(best_submission_key, submission_id)
                return True  # Keep this model
            else:
                # Current model is not better - delete it
                return True  # Delete this model
                
    except Exception as e:
        logger.error(f"Error managing team best model: {e}")
        return False  # Delete on error to be safe


def send_results_to_cpu(result, cpu_server_url, secret_key):
    """Send evaluation results to CPU server"""
    try:
        callback_data = {
            'submission_id': result['submission_id'],
            'team_id': result.get('team_id'),
            'task_id': 2,
            'status': result['status'],
            'score': result.get('score', 0),
            'is_private': result.get('is_private', False),
            'details': result.get('details', {}),
            'timestamp': result['timestamp']
        }
        
        response = requests.post(
            f"{cpu_server_url}/api/gpu-callback/result",
            json=callback_data,
            headers={'X-GPU-Secret': secret_key},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Results sent to CPU server for {result['submission_id']}")
        else:
            logger.warning(f"Failed to send results to CPU: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error sending results to CPU server: {e}")


def process_job(job_data, redis_client, worker_id, batch_size, gpu_memory_fraction, cpu_server_url, secret_key):
    """Process a single evaluation job"""
    try:
        submission_id = job_data['submission_id']
        team_id = job_data.get('team_id')
        model_path = job_data['model_path']
        batch_size_override = job_data.get('batch_size', batch_size)
        
        # Check if this is a private evaluation based on task field
        task_type = job_data.get('task', 'task2')
        is_private = task_type == 'task2_private'
        
        # Set test data path based on private flag
        if is_private:
            test_data_path = '/app/data/test_data/private_test'
        else:
            test_data_path = job_data.get('test_data_path', '/app/data/test_data/public_test')
        
        logger.info(f"Processing submission {submission_id} on test set: {test_data_path} (private={is_private})")
        
        # Evaluate model
        results = evaluate_model(model_path, test_data_path, batch_size_override, gpu_memory_fraction)
        
        # Calculate final score
        score = calculate_score(results)
        
        # Store results
        result = {
            'submission_id': submission_id,
            'team_id': team_id,
            'worker_id': worker_id,
            'score': score,
            'details': results,
            'status': 'completed',
            'is_private': is_private,
            'timestamp': time.time()
        }
        
        # Save to Redis results
        redis_client.hset(
            f'result:{submission_id}',
            mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in result.items()}
        )
        redis_client.expire(f'result:{submission_id}', 7200)  # Expire after 2 hours
        
        # Send results to CPU server
        send_results_to_cpu(result, cpu_server_url, secret_key)
        
        # Manage model storage - keep only best per team
        if team_id:
            keep_model = update_team_best_model(redis_client, team_id, submission_id, score, model_path)
            
            if not keep_model:
                # Delete this model (not the best)
                try:
                    if os.path.exists(model_path):
                        os.remove(model_path)
                        logger.info(f"Deleted model: {model_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete model file: {e}")
        else:
            # No team_id, delete by default
            try:
                if os.path.exists(model_path):
                    os.remove(model_path)
                    logger.warning(f"No team_id, deleted model: {model_path}")
            except Exception as e:
                logger.warning(f"Failed to delete model file: {e}")
        
        logger.info(f"Submission {submission_id} completed with score: {score:.2f}")
        return result
        
    except Exception as e:
        logger.error(f"Job processing failed: {e}", exc_info=True)
        
        # Store error result
        task_type = job_data.get('task', 'task2')
        is_private = task_type == 'task2_private'
        
        error_result = {
            'submission_id': job_data.get('submission_id', 'unknown'),
            'team_id': job_data.get('team_id'),
            'worker_id': worker_id,
            'status': 'failed',
            'error': str(e),
            'is_private': is_private,
            'timestamp': time.time()
        }
        
        redis_client.hset(
            f'result:{job_data.get("submission_id", "unknown")}',
            mapping={k: str(v) for k, v in error_result.items()}
        )
        
        # Send error results to CPU server
        send_results_to_cpu(error_result, cpu_server_url, secret_key)
        
        return error_result
