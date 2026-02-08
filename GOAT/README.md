# GOAT Framework - Submission Helper

The **GOAT Framework** (Gathering Of AI Talent) is a Python package that simplifies submitting solutions and viewing leaderboards for the MLS-GOAT hackathon. It provides a clean, user-friendly API for participants to interact with the hackathon platform.

## 🎯 Purpose

The GOAT framework makes it easy to:
- **Submit Task 1** (Image Reconstruction) solutions
- **Submit Task 2** (Model Inference) solutions  
- **View leaderboards** for both tasks
- **Handle authentication** automatically
- **Validate submissions** before uploading

## 📦 Installation

### Option 1: Install as a Package (Recommended)

```bash
# From the MLS-GOAT root directory
pip install -e GOAT/
```

### Option 2: Add to Python Path

```bash
# Add GOAT to your Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/MLS-GOAT"
```

### Option 3: Direct Import

```python
# Add parent directory to sys.path in your script
import sys
sys.path.append('/path/to/MLS-GOAT')

from GOAT.submit import challenge1, challenge2
from GOAT.leaderboard import getLB_chall1, getLB_chall2
```

## 🚀 Quick Start

### Submitting to Task 1 (Image Reconstruction)

Task 1 requires submitting reconstructed images as PyTorch tensor files.

```python
from GOAT.submit import challenge1

# Submit your reconstruction folder
result = challenge1(
    folder_path="./my_reconstructions",
    team_id="team_awesome",
    password="my_password"
)

print(f"Submission successful!")
print(f"Score (PSNR): {result['score']:.2f} dB")
```

#### Task 1 Requirements:
- **Folder** containing exactly 300 PyTorch tensor files
- **File names**: `sample_0000.pt`, `sample_0001.pt`, ..., `sample_0299.pt`
- **File format**: PyTorch tensors saved with `torch.save()`
- **Content**: Reconstructed images matching the task specifications

### Submitting to Task 2 (Model Inference)

Task 2 requires submitting an ONNX model file.

```python
from GOAT.submit import challenge2

# Submit your ONNX model
result = challenge2(
    model_path="./my_model.onnx",
    team_id="team_awesome",
    password="my_password"
)

print(f"Submission successful!")
print(f"Score: {result['score']:.4f}")
print(f"Inference time: {result.get('inference_time', 'N/A')} ms")
```

#### Task 2 Requirements:
- **File**: Single ONNX model file (`.onnx`)
- **Format**: ONNX format compatible with ONNX Runtime
- **GPU-compatible**: Model will be evaluated on GPU infrastructure

### Viewing Leaderboards

```python
from GOAT.leaderboard import getLB_chall1, getLB_chall2

# View Task 1 leaderboard (top 10 + your position)
getLB_chall1(team_name="team_awesome")

# View Task 2 leaderboard (top 10 + your position)
getLB_chall2(team_name="team_awesome")

# View full leaderboards (top 10 only)
getLB_chall1()  # No team name
getLB_chall2()  # No team name
```

## 📖 Detailed Usage

### Task 1: Image Reconstruction

#### Preparing Your Submission

```python
import torch
import os

# Example: Create submission folder
submission_folder = "./my_task1_submission"
os.makedirs(submission_folder, exist_ok=True)

# Save your reconstructed images as PyTorch tensors
for i in range(300):
    # Your reconstruction logic here
    reconstructed_image = your_model.reconstruct(i)  # Your code
    
    # Save as .pt file
    filename = f"sample_{i:04d}.pt"
    filepath = os.path.join(submission_folder, filename)
    torch.save(reconstructed_image, filepath)

print(f"Created {len(os.listdir(submission_folder))} files")
```

#### Submitting

```python
from GOAT.submit import challenge1

try:
    result = challenge1(
        folder_path="./my_task1_submission",
        team_id="team_awesome",
        password="my_password"
    )
    
    print("✅ Submission successful!")
    print(f"   PSNR Score: {result['score']:.2f} dB")
    print(f"   Submission ID: {result['submission_id']}")
    print(f"   Timestamp: {result['submitted_at']}")
    
except Exception as e:
    print(f"❌ Submission failed: {str(e)}")
```

#### Validation

The framework automatically validates:
- ✅ Folder exists and is accessible
- ✅ Exactly 300 `.pt` files present
- ✅ Files named correctly: `sample_0000.pt` to `sample_0299.pt`
- ✅ No extra or missing files
- ✅ Files are valid PyTorch tensors

### Task 2: Model Inference

#### Preparing Your ONNX Model

```python
import torch
import torch.onnx

# Example: Convert PyTorch model to ONNX
model = YourModel()  # Your trained model
dummy_input = torch.randn(1, 3, 518, 518)  # Adjust to your input shape

torch.onnx.export(
    model,
    dummy_input,
    "my_model.onnx",
    export_params=True,
    opset_version=11,
    do_constant_folding=True,
    input_names=['input'],
    output_names=['output']
)

print("Model exported to my_model.onnx")
```

#### Submitting

```python
from GOAT.submit import challenge2

try:
    result = challenge2(
        model_path="./my_model.onnx",
        team_id="team_awesome",
        password="my_password"
    )
    
    print("✅ Submission successful!")
    print(f"   Score: {result['score']:.4f}")
    print(f"   Submission ID: {result['submission_id']}")
    
    # Additional metrics (if provided)
    if 'metrics' in result:
        print(f"   Inference time: {result['metrics'].get('inference_time')} ms")
        print(f"   Throughput: {result['metrics'].get('throughput')} samples/sec")
    
except Exception as e:
    print(f"❌ Submission failed: {str(e)}")
```

### Viewing Leaderboards

#### Task 1 Leaderboard (PSNR-based)

```python
from GOAT.leaderboard import getLB_chall1

# View as a team member (shows your rank)
getLB_chall1(team_name="team_awesome")

# Output:
# === Task 1 Leaderboard (PSNR) - Top 10 ===
# rank  team_name       score
#    1  team_alpha     35.42
#    2  team_beta      34.89
#    3  team_awesome   34.12
#    ...
# Your stats (team_awesome): Rank 3, Score 34.12
```

#### Task 2 Leaderboard (Performance-based)

```python
from GOAT.leaderboard import getLB_chall2

# View as a team member (shows your rank)
getLB_chall2(team_name="team_awesome")

# Output:
# === Task 2 Leaderboard (Model Performance) - Top 10 ===
# rank  team_name       score
#    1  team_neural    0.9521
#    2  team_awesome   0.9487
#    3  team_deep      0.9456
#    ...
# Your stats (team_awesome): Rank 2, Score 0.9487
```

## 🔧 Configuration

### API Endpoint Configuration

By default, the framework uses the hosted API. To change it:

```python
# In submit.py
CPU_API_URL = "https://your-backend-url.com/api"

# In leaderboard.py
API_URL = "https://your-backend-url.com/api"
```

Or set it at runtime:

```python
import GOAT.submit as submit
import GOAT.leaderboard as leaderboard

submit.CPU_API_URL = "http://localhost:8000"
leaderboard.API_URL = "http://localhost:8000"
```

## 📚 API Reference

### submit.challenge1()

Submit Task 1 (Image Reconstruction) solution.

**Parameters:**
- `folder_path` (str): Path to folder containing `.pt` files
- `team_id` (str): Your team name/ID
- `password` (str): Your team password

**Returns:**
- dict: Submission result
  ```python
  {
      'submission_id': 123,
      'score': 34.56,  # PSNR in dB
      'submitted_at': '2024-01-01T12:00:00',
      'task': 1
  }
  ```

**Raises:**
- `ValueError`: Invalid folder path or file validation failed
- `Exception`: Login failed or submission error

### submit.challenge2()

Submit Task 2 (Model Inference) solution.

**Parameters:**
- `model_path` (str): Path to ONNX model file
- `team_id` (str): Your team name/ID
- `password` (str): Your team password

**Returns:**
- dict: Submission result
  ```python
  {
      'submission_id': 124,
      'score': 0.9487,
      'submitted_at': '2024-01-01T12:05:00',
      'task': 2,
      'metrics': {
          'inference_time': 15.3,  # ms
          'throughput': 65.4  # samples/sec
      }
  }
  ```

**Raises:**
- `ValueError`: Invalid model path
- `Exception`: Login failed or submission error

### leaderboard.getLB_chall1()

View Task 1 leaderboard.

**Parameters:**
- `team_name` (str, optional): Your team name to highlight your position

**Output:**
- Prints formatted leaderboard to console

### leaderboard.getLB_chall2()

View Task 2 leaderboard.

**Parameters:**
- `team_name` (str, optional): Your team name to highlight your position

**Output:**
- Prints formatted leaderboard to console

## 🔍 Behind the Scenes

### Authentication Flow

```python
def _login(team_id, password):
    """Authenticate and get JWT token"""
    response = requests.post(
        f"{CPU_API_URL}/auth/login",
        json={"name": team_id, "password": password}
    )
    return response.json()["access_token"]
```

The framework:
1. Sends login request to backend
2. Receives JWT token
3. Includes token in subsequent requests
4. Token expires after configured time

### File Validation (Task 1)

```python
# Expected files: sample_0000.pt to sample_0299.pt
EXPECTED_RANGE = set(range(0, 300))

# Validation checks:
1. Folder exists and is accessible
2. All files match pattern: sample_XXXX.pt
3. Exactly 300 files present
4. No duplicates or missing numbers
5. All files are valid PyTorch tensors
```

### Submission Process

**Task 1:**
1. Validate folder and files
2. Create ZIP archive of folder
3. Authenticate with backend
4. Upload ZIP file
5. Backend extracts, validates, and scores
6. Return score and submission details

**Task 2:**
1. Validate ONNX file exists
2. Authenticate with backend
3. Upload ONNX file
4. Backend forwards to GPU service
5. GPU service evaluates model
6. Return score and metrics

## 🐛 Troubleshooting

### Login Failed

```python
# Error: "Login failed: Incorrect team name or password"
# Solution: Check credentials
challenge1(
    folder_path="...",
    team_id="team_awesome",  # ← Check spelling
    password="correct_password"  # ← Verify password
)
```

### File Validation Failed

```python
# Error: "Expected 300 files but found 299"
# Solution: Ensure all files are present

# List files to check
import os
files = sorted(os.listdir("./my_folder"))
print(f"Found {len(files)} files")
print(f"First: {files[0]}, Last: {files[-1]}")
```

### Network Errors

```python
# Error: Connection refused or timeout
# Solution: Check API URL and network connectivity

import requests
response = requests.get("https://mls-goat.eastus2.cloudapp.azure.com/api/")
print(f"Status: {response.status_code}")  # Should be 200
```

### File Too Large

```python
# Error: File too large to upload
# Solution: Check model size or compression

import os
model_size = os.path.getsize("my_model.onnx") / (1024 * 1024)  # MB
print(f"Model size: {model_size:.2f} MB")

# If too large, optimize your model:
# - Reduce precision (FP16 instead of FP32)
# - Prune unnecessary layers
# - Use model compression techniques
```

## 💡 Tips & Best Practices

### For Task 1

1. **Validate locally first**:
   ```python
   import os
   files = os.listdir("./my_folder")
   assert len(files) == 300, f"Expected 300 files, found {len(files)}"
   ```

2. **Use progress bars**:
   ```python
   from tqdm import tqdm
   for i in tqdm(range(300)):
       # Save files with progress indicator
       torch.save(image, f"sample_{i:04d}.pt")
   ```

3. **Test with a small subset first**:
   Create a test folder with a few files to verify the process works

### For Task 2

1. **Test ONNX model locally**:
   ```python
   import onnxruntime as ort
   session = ort.InferenceSession("my_model.onnx")
   # Test inference
   ```

2. **Optimize for GPU**:
   - Use GPU-compatible operations
   - Batch operations when possible
   - Avoid dynamic shapes if possible

3. **Check model size**:
   ```python
   import os
   size_mb = os.path.getsize("my_model.onnx") / (1024**2)
   print(f"Model size: {size_mb:.2f} MB")
   ```

## 📊 Example Workflow

### Complete Task 1 Workflow

```python
import torch
import os
from GOAT.submit import challenge1
from GOAT.leaderboard import getLB_chall1

# 1. Create submission folder
submission_dir = "./task1_submission"
os.makedirs(submission_dir, exist_ok=True)

# 2. Generate reconstructions
print("Generating reconstructions...")
for i in range(300):
    # Your reconstruction code
    image = your_reconstruction_function(i)
    torch.save(image, f"{submission_dir}/sample_{i:04d}.pt")

# 3. Validate locally
files = os.listdir(submission_dir)
print(f"Created {len(files)} files")
assert len(files) == 300, "Missing files!"

# 4. Submit
print("Submitting...")
result = challenge1(
    folder_path=submission_dir,
    team_id="team_awesome",
    password="my_password"
)
print(f"✅ Score: {result['score']:.2f} dB")

# 5. Check leaderboard
print("\nChecking leaderboard...")
getLB_chall1(team_name="team_awesome")
```

### Complete Task 2 Workflow

```python
import torch.onnx
from GOAT.submit import challenge2
from GOAT.leaderboard import getLB_chall2

# 1. Train and export model
print("Exporting model to ONNX...")
torch.onnx.export(model, dummy_input, "my_model.onnx")

# 2. Validate ONNX model
import onnxruntime as ort
session = ort.InferenceSession("my_model.onnx")
print(f"Model inputs: {session.get_inputs()[0].name}")
print(f"Model outputs: {session.get_outputs()[0].name}")

# 3. Submit
print("Submitting...")
result = challenge2(
    model_path="my_model.onnx",
    team_id="team_awesome",
    password="my_password"
)
print(f"✅ Score: {result['score']:.4f}")

# 4. Check leaderboard
print("\nChecking leaderboard...")
getLB_chall2(team_name="team_awesome")
```

## 📄 License

Part of the MLS-GOAT hackathon platform.

---

**GOAT Framework - Making hackathon submissions simple and straightforward! 🐐**
