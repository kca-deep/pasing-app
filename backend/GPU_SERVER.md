# Dolphin GPU Server Setup Guide

This document explains how to set up and run the Dolphin GPU server on a remote machine.

## Overview

The Dolphin GPU server (`gpu_server.py`) is a standalone FastAPI service that runs Dolphin 1.5 model inference on a GPU-equipped machine. The main parsing application communicates with this server via HTTP.

## Prerequisites

- GPU-equipped machine with CUDA support
- Python 3.9+
- CUDA 11.8+ (for PyTorch GPU support)

## Installation (GPU Server Machine)

### 1. Install Dependencies

```bash
pip install fastapi uvicorn transformers torch pillow
```

### 2. Download Dolphin Model

```bash
# Install Hugging Face CLI
pip install huggingface-hub

# Download Dolphin 1.5 model (~2GB)
huggingface-cli download ByteDance/Dolphin-1.5 --local-dir ./dolphin_models/Dolphin-1.5
```

### 3. Copy Server File

Transfer `backend/gpu_server.py` to your GPU server machine.

## Running the Server

### Basic Usage

```bash
python gpu_server.py \
  --model-path ./dolphin_models/Dolphin-1.5 \
  --host 0.0.0.0 \
  --port 8001
```

### Command Line Arguments

- `--model-path`: Path to Dolphin-1.5 model directory (required)
- `--host`: Server host address (default: 0.0.0.0)
- `--port`: Server port (default: 8001)
- `--log-level`: Logging level - debug, info, warning, error (default: info)

### Example with Custom Settings

```bash
python gpu_server.py \
  --model-path /models/Dolphin-1.5 \
  --host 0.0.0.0 \
  --port 8002 \
  --log-level debug
```

## API Endpoints

### `GET /`
Server status and model information

**Response:**
```json
{
  "status": "running",
  "service": "Dolphin GPU Server",
  "version": "1.0.0",
  "model_loaded": true,
  "device": "cuda",
  "cuda_available": true
}
```

### `GET /health`
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cuda"
}
```

### `POST /infer`
Run Dolphin inference on an image

**Request:**
```json
{
  "prompt": "Parse the reading order of this document.",
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "max_length": 4096,
  "temperature": 0.0
}
```

**Response:**
```json
{
  "text": "[x1,y1,x2,y2][header][PAIR_SEP]...",
  "device": "cuda",
  "model_loaded": true
}
```

## Client Configuration

On the parsing application backend, set the environment variable:

```bash
# backend/.env
DOLPHIN_GPU_SERVER=http://your-gpu-server-ip:8001
```

The backend will automatically check server availability on startup.

## Performance Metrics

| Configuration | Device | 1 Page | 10 Pages |
|---------------|--------|--------|----------|
| Local CPU | Intel i7 | ~60s | ~10min |
| Local GPU | RTX 3060 | ~8s | ~80s |
| **Remote GPU** | **RTX 4090** | **~3s** | **~30s** |

## Troubleshooting

### Server Not Reachable

**Symptoms:**
```
⚠️ Dolphin GPU Server not available
```

**Solutions:**
1. Check if server is running:
   ```bash
   curl http://your-gpu-server-ip:8001/health
   ```

2. Verify firewall settings:
   ```bash
   # Ubuntu/Debian
   sudo ufw allow 8001

   # CentOS/RHEL
   sudo firewall-cmd --add-port=8001/tcp --permanent
   sudo firewall-cmd --reload
   ```

3. Test network connectivity:
   ```bash
   ping your-gpu-server-ip
   telnet your-gpu-server-ip 8001
   ```

### GPU Out of Memory

**Symptoms:**
```
torch.cuda.OutOfMemoryError: CUDA out of memory
```

**Solutions:**
- Close other GPU processes: `nvidia-smi` to check
- Model loads in FP16 by default to save memory
- For 8-bit quantization: modify `gpu_server.py` model loading

### Slow Inference

**Causes:**
- GPU doesn't support FP16
- Other processes using GPU
- CPU fallback mode

**Check:**
```bash
nvidia-smi
```

**Solution:**
- Terminate conflicting processes
- Verify CUDA availability in server logs

## Security Considerations

### Production Deployment

1. **Use HTTPS** (requires SSL certificates)
2. **Add API key authentication** (future update)
3. **Use VPN or firewall** to restrict access
4. **Monitor resource usage** to prevent abuse

### Recommended Setup

```bash
# Use reverse proxy (nginx) with SSL
# Restrict access by IP whitelist
# Set up monitoring (Prometheus + Grafana)
```

## License

Apache 2.0

## Support

For issues and feature requests, please use the project's issue tracker.
