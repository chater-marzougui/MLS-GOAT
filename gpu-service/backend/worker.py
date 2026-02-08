"""Main worker process for GPU model evaluation"""

import os
import sys
import time
import json
import logging

from queue_handler import get_redis_client, process_job

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=f'[Worker-{os.getenv("WORKER_ID", "0")}] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
WORKER_ID = os.getenv('WORKER_ID', '0')
GPU_MEMORY_FRACTION = float(os.getenv('GPU_MEMORY_FRACTION', 0.143))
BATCH_SIZE = int(os.getenv('BATCH_SIZE', 8))
CPU_SERVER_URL = os.getenv('CPU_SERVER_URL', 'https://mls-goat.eastus2.cloudapp.azure.com')
GPU_SCORER_SECRET_KEY = os.getenv('GPU_SCORER_SECRET_KEY')


def main():
    """Main worker loop"""
    logger.info(f"Worker {WORKER_ID} starting...")
    logger.info(f"GPU Memory Fraction: {GPU_MEMORY_FRACTION}")
    logger.info(f"Batch Size: {BATCH_SIZE}")
    logger.info(f"Redis Host: {REDIS_HOST}")
    logger.info(f"CPU Server: {CPU_SERVER_URL}")
    
    # Create Redis client
    redis_client = get_redis_client(REDIS_HOST, REDIS_PORT)
    
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
                process_job(
                    job_data=job_data,
                    redis_client=redis_client,
                    worker_id=WORKER_ID,
                    batch_size=BATCH_SIZE,
                    gpu_memory_fraction=GPU_MEMORY_FRACTION,
                    cpu_server_url=CPU_SERVER_URL,
                    secret_key=GPU_SCORER_SECRET_KEY
                )
                
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
