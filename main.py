"""FastAPI entrypoint for the DialoGPT chatbot web app."""

import asyncio
import logging
from contextlib import asynccontextmanager
from functools import partial

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from config import config
from model import ChatModel

logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=[config.RATE_LIMIT])
templates = Jinja2Templates(directory="templates")

chat_model: ChatModel | None = None


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message text.")

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Message cannot be empty.")
        if len(normalized) > config.MAX_INPUT_LENGTH:
            raise ValueError(
                f"Message exceeds max length of {config.MAX_INPUT_LENGTH} characters."
            )

        lowered = normalized.lower()
        blocked_patterns = ("<script>", "javascript:", "onerror=")
        if any(pattern in lowered for pattern in blocked_patterns):
            raise ValueError("Potentially unsafe content detected in message.")
        return normalized


class ChatResponse(BaseModel):
    response: str
    status: str = "success"


@asynccontextmanager
async def lifespan(_: FastAPI):
    global chat_model
    logger.info("Starting application and loading model.")
    chat_model = ChatModel(
        model_name=config.MODEL_NAME,
        max_history=config.MAX_HISTORY_LENGTH,
    )
    try:
        yield
    finally:
        logger.info("Shutting down application and releasing model.")
        chat_model = None


app = FastAPI(title="AI Chatbot", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    logger.warning("HTTP error on %s: %s", request.url.path, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status": "error"},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error.", "status": "error"},
    )


@app.get("/", response_class=HTMLResponse)
@limiter.limit(config.RATE_LIMIT)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "max_length": config.MAX_INPUT_LENGTH},
    )


@app.post("/chat", response_model=ChatResponse)
@limiter.limit(config.RATE_LIMIT_CHAT)
async def chat(request: Request, payload: ChatRequest) -> ChatResponse:
    if chat_model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded yet.",
        )

    loop = asyncio.get_running_loop()
    inference_call = partial(chat_model.generate_response, payload.message)

    try:
        response_text = await asyncio.wait_for(
            loop.run_in_executor(None, inference_call),
            timeout=config.MODEL_TIMEOUT,
        )
    except asyncio.TimeoutError as exc:
        logger.error("Model inference timed out.")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Model response timed out. Please try again.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected chat inference failure.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate a response.",
        ) from exc

    return ChatResponse(response=response_text, status="success")


@app.post("/clear")
@limiter.limit(config.RATE_LIMIT)
async def clear_chat(request: Request) -> JSONResponse:
    if chat_model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded yet.",
        )

    chat_model.clear_history()
    return JSONResponse(content={"status": "success", "message": "Chat history cleared."})


@app.get("/health")
@limiter.limit(config.RATE_LIMIT)
async def health_check(request: Request) -> JSONResponse:
    model_loaded = chat_model is not None
    return JSONResponse(
        content={
            "status": "healthy",
            "model_name": config.MODEL_NAME,
            "max_history": config.MAX_HISTORY_LENGTH,
            "model_loaded": model_loaded,
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
    )
