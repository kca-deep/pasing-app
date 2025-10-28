"""
Dolphin GPU Server
원격 GPU 서버에서 실행할 FastAPI 서버

실행 방법 (GPU 서버에서):
    pip install fastapi uvicorn transformers torch pillow
    python gpu_server.py --model-path /path/to/Dolphin-1.5 --port 8001
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
from transformers import AutoProcessor, VisionEncoderDecoderModel
from PIL import Image
import io
import base64
import argparse
import logging
import os

# 환경변수에서 기본 설정 로드
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GPU 서버 기본 설정
DEFAULT_MAX_LENGTH = int(os.getenv("DOLPHIN_MAX_LENGTH", "4096"))
DEFAULT_TEMPERATURE = float(os.getenv("DOLPHIN_TEMPERATURE", "0.0"))
USE_FP16 = os.getenv("DOLPHIN_USE_FP16", "True").lower() in ("true", "1", "yes")

app = FastAPI(title="Dolphin GPU Server", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model variables
model = None
processor = None
device = None


class InferenceRequest(BaseModel):
    """추론 요청"""
    prompt: str
    image_base64: str
    max_length: int = DEFAULT_MAX_LENGTH
    temperature: float = DEFAULT_TEMPERATURE


class InferenceResponse(BaseModel):
    """추론 응답"""
    text: str
    device: str
    model_loaded: bool


@app.on_event("startup")
async def load_model():
    """서버 시작 시 모델 로드"""
    global model, processor, device

    logger.info("=" * 60)
    logger.info("🐬 Loading Dolphin Model...")
    logger.info("=" * 60)

    try:
        model_path = app.state.model_path

        # 디바이스 설정
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Device: {device}")

        # 모델 및 프로세서 로드
        logger.info(f"Loading from: {model_path}")
        processor = AutoProcessor.from_pretrained(model_path, use_fast=True)
        model = VisionEncoderDecoderModel.from_pretrained(model_path)
        model.eval()

        # GPU로 이동 및 최적화
        model.to(device)
        if device == "cuda" and USE_FP16:
            model = model.half()  # FP16 for faster inference
            logger.info("✅ Model loaded on GPU (FP16)")
        elif device == "cuda":
            logger.info("✅ Model loaded on GPU (FP32)")
        else:
            logger.info("⚠️ Model loaded on CPU (FP32)")

        logger.info("=" * 60)
        logger.info("✅ Dolphin Server Ready!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}", exc_info=True)
        raise


@app.get("/")
async def root():
    """서버 상태 확인"""
    return {
        "status": "running",
        "service": "Dolphin GPU Server",
        "version": "1.0.0",
        "model_loaded": model is not None,
        "device": device,
        "cuda_available": torch.cuda.is_available()
    }


@app.get("/health")
async def health():
    """Health check"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return {
        "status": "healthy",
        "model_loaded": True,
        "device": device
    }


@app.post("/infer", response_model=InferenceResponse)
async def infer(request: InferenceRequest):
    """Dolphin 추론 엔드포인트"""
    global model, processor, device

    if model is None or processor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Base64 디코딩 → PIL Image
        image_data = base64.b64decode(request.image_base64)
        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        # 이미지 전처리
        pixel_values = processor(image, return_tensors="pt").pixel_values
        if device == "cuda" and USE_FP16:
            pixel_values = pixel_values.half().cuda()
        else:
            pixel_values = pixel_values.to(device)

        # 프롬프트 형식 (Dolphin 공식 형식)
        formatted_prompt = f"<s>{request.prompt} <Answer/>"
        prompt_ids = processor.tokenizer(
            formatted_prompt,
            add_special_tokens=False,
            return_tensors="pt"
        ).input_ids.to(device)

        decoder_attention_mask = torch.ones_like(prompt_ids)

        # 추론
        with torch.no_grad():
            outputs = model.generate(
                pixel_values=pixel_values,
                decoder_input_ids=prompt_ids,
                decoder_attention_mask=decoder_attention_mask,
                min_length=1,
                max_length=request.max_length,
                pad_token_id=processor.tokenizer.pad_token_id,
                eos_token_id=processor.tokenizer.eos_token_id,
                use_cache=True,
                bad_words_ids=[[processor.tokenizer.unk_token_id]],
                return_dict_in_generate=True,
                do_sample=False,
                num_beams=1
            )

        # 결과 디코딩
        sequence = processor.tokenizer.batch_decode(outputs.sequences, skip_special_tokens=False)[0]
        sequence = sequence.replace(formatted_prompt, "").replace("<pad>", "").replace("</s>", "").strip()

        return InferenceResponse(
            text=sequence,
            device=device,
            model_loaded=True
        )

    except Exception as e:
        logger.error(f"Inference error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dolphin GPU Server")
    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Path to Dolphin-1.5 model directory"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("GPU_SERVER_HOST", "0.0.0.0"),
        help="Server host (default: from GPU_SERVER_HOST or 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("GPU_SERVER_PORT", "8001")),
        help="Server port (default: from GPU_SERVER_PORT or 8001)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.getenv("GPU_SERVER_LOG_LEVEL", "info"),
        choices=["debug", "info", "warning", "error"],
        help="Logging level (default: from GPU_SERVER_LOG_LEVEL or info)"
    )

    args = parser.parse_args()

    # Store model path in app state
    app.state.model_path = args.model_path

    # Run server
    import uvicorn
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=args.log_level
    )
