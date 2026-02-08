"""Video API endpoints - including upscale functionality"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import asyncio
from curl_cffi.requests import AsyncSession

from app.core.config import setting
from app.core.logger import logger
from app.services.grok.statsig import get_dynamic_headers
from app.core.exception import GrokApiException


router = APIRouter()


class UpscaleRequest(BaseModel):
    video_id: str


class UpscaleResponse(BaseModel):
    hd_media_url: str


@router.post("/videos/upscale", response_model=UpscaleResponse)
async def upscale_video(request: UpscaleRequest):
    """Upscale video to HD quality"""
    video_id = request.video_id
    if not video_id:
        raise HTTPException(status_code=400, detail="video_id is required")

    try:
        from app.services.grok.token import token_manager
        
        # First, try to get the token that generated this video
        auth_token = token_manager.get_video_token(video_id)
        
        if auth_token:
            logger.info(f"[Upscale] Using original token for video: {video_id[:20]}...")
        else:
            # Fallback to load-balanced token selection
            logger.warning(f"[Upscale] No mapped token found, using fallback for video: {video_id}")
            auth_token = token_manager.get_token("grok-imagine-0.9")
        
        if not auth_token:
            raise HTTPException(status_code=401, detail="No authentication token available")

        # Build headers following existing pattern
        cf = setting.grok_config.get("cf_clearance", "")
        headers = {
            **get_dynamic_headers("/rest/media/video/upscale"),
            "Cookie": f"{auth_token};{cf}" if cf else auth_token,
            "Referer": f"https://grok.com/imagine/post/{video_id}"
        }

        # Prepare request body
        payload = {"videoId": video_id}

        # Get proxy configuration
        from app.core.proxy_pool import proxy_pool
        proxy = await proxy_pool.get_proxy() if proxy_pool._enabled else None
        if not proxy:
            # Fallback to settings proxy
            proxy_url = setting.grok_config.get("proxy_url", "")
            proxy = proxy_url if proxy_url else None
        
        proxies = {"http": proxy, "https": proxy} if proxy else None

        logger.info(f"[Upscale] Starting upscale for video: {video_id}")

        # Make request with extended timeout (upscale processing takes time)
        async with AsyncSession() as session:
            response = await session.post(
                "https://grok.com/rest/media/video/upscale",
                headers=headers,
                json=payload,
                impersonate="chrome133a",
                timeout=120,  # Increased timeout for upscale processing
                proxies=proxies
            )

            logger.info(f"[Upscale] Response status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                hd_url = result.get("hdMediaUrl")
                if hd_url:
                    logger.info(f"[Upscale] Success: {video_id} -> {hd_url}")
                    
                    # Download and cache the HD video
                    from app.services.grok.cache import video_cache_service
                    from urllib.parse import urlparse
                    
                    # Extract path from HD URL
                    # Example: https://assets.grok.com/users/xxx/generated/yyy/generated_video_hd.mp4
                    parsed_url = urlparse(hd_url)
                    video_path = parsed_url.path  # /users/xxx/generated/yyy/generated_video_hd.mp4
                    
                    logger.info(f"[Upscale] Downloading HD video: {video_path}")
                    
                    # Download and cache the video
                    cached_path = await video_cache_service.download_video(video_path, auth_token)
                    
                    if cached_path:
                        # Generate localhost URL
                        # Convert path: /users/xxx/generated/yyy/generated_video_hd.mp4
                        # To: users-xxx-generated-yyy-generated_video_hd.mp4
                        local_filename = video_path.lstrip('/').replace('/', '-')
                        
                        # Get base URL from settings
                        base_url = setting.global_config.get("base_url", "")
                        if not base_url:
                            # Fallback to request host if available
                            base_url = "http://localhost:8017"
                        
                        local_url = f"{base_url}/images/{local_filename}"
                        
                        logger.info(f"[Upscale] HD video cached successfully: {local_url}")
                        return UpscaleResponse(hd_media_url=local_url)
                    else:
                        # If caching fails, return original Grok URL as fallback
                        logger.warning(f"[Upscale] Failed to cache HD video, returning original URL")
                        return UpscaleResponse(hd_media_url=hd_url)
                else:
                    logger.error(f"[Upscale] No HD URL in response: {result}")
                    raise HTTPException(status_code=500, detail="No HD media URL returned")

            elif response.status_code == 403:
                logger.error(f"[Upscale] 403 Forbidden - IP may be blocked")
                raise HTTPException(status_code=403, detail="Access forbidden - IP may be blocked or need proxy")

            elif response.status_code == 401:
                logger.error(f"[Upscale] 401 Unauthorized - Invalid token")
                raise HTTPException(status_code=401, detail="Authentication failed")

            elif response.status_code == 404:
                logger.error(f"[Upscale] 404 Not Found - Video ID may be invalid: {video_id}")
                raise HTTPException(status_code=404, detail=f"Video not found: {video_id}")

            else:
                error_text = response.text[:200] if response.text else "No error message"
                logger.error(f"[Upscale] Unexpected status {response.status_code}: {error_text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Upscale request failed: {error_text}"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Upscale] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
