"""Chat API Router - OpenAI compatible chat interface"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from fastapi.responses import StreamingResponse

from app.core.auth import auth_manager
from app.core.exception import GrokApiException
from app.core.logger import logger
from app.services.grok.client import GrokClient
from app.models.openai_schema import OpenAIChatRequest


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/completions", response_model=None)
async def chat_completions(request: OpenAIChatRequest, _: Optional[str] = Depends(auth_manager.verify)):
    """Create chat completion (supports streaming and non-streaming)"""
    try:
        logger.info("[Chat] Received chat request")

        # Call Grok client
        result = await GrokClient.openai_to_grok(request.model_dump())
        
        # Streaming response
        if request.stream:
            return StreamingResponse(
                content=result,
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        # Non-streaming response
        return result
        
    except GrokApiException as e:
        logger.error(f"[Chat] Grok API error: {e} - Details: {e.details}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": str(e),
                    "type": e.error_code or "grok_api_error",
                    "code": e.error_code or "unknown"
                }
            }
        )
    except Exception as e:
        logger.error(f"[Chat] Process failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "Internal server error",
                    "type": "internal_error",
                    "code": "internal_server_error"
                }
            }
        )
