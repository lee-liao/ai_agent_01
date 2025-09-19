import os
import logging
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()


class Message(BaseModel):
    role: str = Field(..., description="One of: system|user|assistant")
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = Field(default="gpt-4o-mini")
    temperature: Optional[float] = 0.3


class ChatResponse(BaseModel):
    reply: str


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


app = FastAPI(title="Exercise 2 Chat Backend", version="0.1.0")

# CORS
default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:4000",
    "http://127.0.0.1:4000",
]
extra_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
origins = default_origins + extra_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    logger.info("/chat endpoint called")
    try:
        from openai import OpenAI
        logger.debug("OpenAI module imported successfully")
    except Exception as e:
        logger.error(f"Failed to import OpenAI module: {e}")
        raise HTTPException(status_code=500, detail=f"OpenAI package not available: {e}")

    try:
        api_key = require_env("OPENAI_API_KEY")
        logger.info(f"API Key retrieved (last 5 chars): ...{api_key[-5:] if api_key else 'None'}")
        
        logger.debug("Creating OpenAI client")
        client = OpenAI(api_key=api_key)
        logger.debug("OpenAI client created successfully")
        
        logger.debug(f"Request messages: {req.messages}")
        logger.debug(f"Request model: {req.model}")
        logger.debug(f"Request temperature: {req.temperature}")
        
        completion = client.chat.completions.create(
            model=req.model or "gpt-4o-mini",
            messages=[m.dict() for m in req.messages],
            temperature=req.temperature or 0.3,
        )
        logger.debug("OpenAI completion received successfully")
        reply_content = completion.choices[0].message.content or ""
        logger.debug(f"Reply content: {reply_content}")
        return ChatResponse(reply=reply_content)
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {e}")