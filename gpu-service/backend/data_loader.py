"""Data loading and caching for test images and ground truth"""

import numpy as np
from pathlib import Path
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# Global cache for test data (loaded once per worker)
TEST_DATA_CACHE = {}
GROUND_TRUTH_CACHE = {}


def load_test_data(test_data_path):
    """Load test dataset (images) for evaluation from disk and cache in memory"""
    global TEST_DATA_CACHE
    
    # Return cached data if available
    if test_data_path in TEST_DATA_CACHE:
        logger.info(f"Using cached test data from {test_data_path} with {len(TEST_DATA_CACHE[test_data_path][0])} samples")
        return TEST_DATA_CACHE[test_data_path]
    
    try:
        logger.info(f"Loading test images from: {test_data_path}")
        
        # Load all *_image.png files from the test_data directory
        image_files = sorted(Path(test_data_path).glob("*_image.png"))
        
        if not image_files:
            raise ValueError(f"No *_image.png files found in {test_data_path}")
        
        logger.info(f"Found {len(image_files)} test images")
        
        # Load all images into a list with preprocessing
        samples = []
        sample_names = []
        
        for image_path in image_files:
            # Load image
            img = Image.open(image_path).convert('RGB')
            img_array = np.array(img, dtype=np.float32)
            
            # Normalize to [0, 1] range if needed
            if img_array.max() > 1.0:
                img_array = img_array / 255.0
            
            # Convert HWC to CHW format (channels first)
            img_array = np.transpose(img_array, (2, 0, 1))
            
            samples.append(img_array)
            sample_names.append(image_path.stem.replace('_image', ''))
        
        # Stack all samples into a single array
        test_data = np.stack(samples, axis=0).astype(np.float32)
        
        logger.info(f"Loaded test data with shape: {test_data.shape}, dtype: {test_data.dtype}")
        
        # Cache the test data for future use
        TEST_DATA_CACHE[test_data_path] = (test_data, sample_names)
        
        return test_data, sample_names
    except Exception as e:
        logger.error(f"Failed to load test data: {e}")
        raise


def load_ground_truth(test_data_path, sample_names):
    """Load ground truth depth maps for evaluation"""
    global GROUND_TRUTH_CACHE
    
    # Return cached ground truth if available
    if test_data_path in GROUND_TRUTH_CACHE:
        logger.info(f"Using cached ground truth from {test_data_path}")
        return GROUND_TRUTH_CACHE[test_data_path]
    
    try:
        logger.info(f"Loading ground truth depth maps from: {test_data_path}")
        
        ground_truths = []
        
        for sample_name in sample_names:
            depth_map_path = Path(test_data_path) / f"{sample_name}_depth_map.png"
            
            if not depth_map_path.exists():
                raise ValueError(f"Ground truth not found: {depth_map_path}")
            
            # Load depth map as grayscale
            depth_map = Image.open(depth_map_path).convert('L')
            depth_array = np.array(depth_map, dtype=np.float32)
            
            # Normalize to [0, 1] range if needed
            if depth_array.max() > 1.0:
                depth_array = depth_array / 255.0
            
            ground_truths.append(depth_array)
        
        ground_truth_data = np.stack(ground_truths, axis=0)
        
        logger.info(f"Loaded ground truth with shape: {ground_truth_data.shape}, dtype: {ground_truth_data.dtype}")
        
        # Cache the ground truth
        GROUND_TRUTH_CACHE[test_data_path] = ground_truth_data
        
        return ground_truth_data
    except Exception as e:
        logger.error(f"Failed to load ground truth: {e}")
        raise
