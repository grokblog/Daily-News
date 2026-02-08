"""Grok API Client - Handle OpenAI to Grok request conversion and response processing"""

import asyncio
import orjson
from typing import Dict, List, Tuple, Any, Optional
from curl_cffi import requests as curl_requests

from app.core.config import setting
from app.core.logger import logger
from app.models.grok_models import Models
from app.services.grok.processer import GrokResponseProcessor
from app.services.grok.statsig import get_dynamic_headers
from app.services.grok.token import token_manager
from app.services.grok.upload import ImageUploadManager
from app.services.grok.create import PostCreateManager
from app.core.exception import GrokApiException


# 常量
API_ENDPOINT = "https://grok.com/rest/app-chat/conversations/new"
TIMEOUT = 120
BROWSER = "chrome120"
MAX_RETRY = 3
MAX_UPLOADS = 20  # 提高并发上传限制以支持更高并发


class GrokClient:
    """Grok API Client"""
    
    _upload_sem = None  # 延迟初始化

    @staticmethod
    def _get_upload_semaphore():
        """Get upload semaphore (dynamic config)"""
        if GrokClient._upload_sem is None:
            # 从配置读取，如果不可用则使用默认值
            max_concurrency = setting.global_config.get("max_upload_concurrency", MAX_UPLOADS)
            GrokClient._upload_sem = asyncio.Semaphore(max_concurrency)
            logger.debug(f"[Client] Initialized upload concurrency limit: {max_concurrency}")
        return GrokClient._upload_sem

    @staticmethod
    async def openai_to_grok(request: dict):
        """Convert OpenAI request to Grok request"""
        model = request["model"]
        content, images = GrokClient._extract_content(request["messages"])
        stream = request.get("stream", False)
        
        # 获取模型信息
        info = Models.get_model_info(model)
        grok_model, mode = Models.to_grok(model)
        is_video = info.get("is_video_model", False)
        
        # 视频模型限制
        if is_video and len(images) > 1:
            logger.warning(f"[Client] Video model only supports 1 image, truncated to first 1")
            images = images[:1]
        
        return await GrokClient._retry(model, content, images, grok_model, mode, is_video, stream)

    @staticmethod
    async def _retry(model: str, content: str, images: List[str], grok_model: str, mode: str, is_video: bool, stream: bool):
        """Retry request"""
        last_err = None

        for i in range(MAX_RETRY):
            try:
                token = token_manager.get_token(model)
                img_ids, img_uris = await GrokClient._upload(images, token)

                # 视频模型创建会话
                post_id = None
                if is_video and img_ids and img_uris:
                    post_id = await GrokClient._create_post(img_ids[0], img_uris[0], token)

                payload = GrokClient._build_payload(content, grok_model, mode, img_ids, img_uris, is_video, post_id)
                return await GrokClient._request(payload, token, model, stream, post_id)

            except GrokApiException as e:
                last_err = e
                # 检查是否可重试
                if e.error_code not in ["HTTP_ERROR", "NO_AVAILABLE_TOKEN"]:
                    raise

                status = e.context.get("status") if e.context else None
                retry_codes = setting.grok_config.get("retry_status_codes", [401, 429])
                
                if status not in retry_codes:
                    raise

                if i < MAX_RETRY - 1:
                    logger.warning(f"[Client] Failed (status:{status}), retry {i+1}/{MAX_RETRY}")
                    await asyncio.sleep(0.5)

        raise last_err or GrokApiException("Request failed", "REQUEST_ERROR")

    @staticmethod
    def _extract_content(messages: List[Dict]) -> Tuple[str, List[str]]:
        """Extract text and images"""
        texts, images = [], []
        
        for msg in messages:
            content = msg.get("content", "")
            
            if isinstance(content, list):
                for item in content:
                    if item.get("type") == "text":
                        texts.append(item.get("text", ""))
                    elif item.get("type") == "image_url":
                        if url := item.get("image_url", {}).get("url"):
                            images.append(url)
            else:
                texts.append(content)
        
        return "".join(texts), images

    @staticmethod
    async def _upload(urls: List[str], token: str) -> Tuple[List[str], List[str]]:
        """Concurrent image upload"""
        if not urls:
            return [], []
        
        async def upload_limited(url):
            async with GrokClient._get_upload_semaphore():
                return await ImageUploadManager.upload(url, token)
        
        results = await asyncio.gather(*[upload_limited(u) for u in urls], return_exceptions=True)
        
        ids, uris = [], []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.warning(f"[Client] Upload failed: {url} - {result}")
            elif isinstance(result, tuple) and len(result) == 2:
                fid, furi = result
                if fid:
                    ids.append(fid)
                    uris.append(furi)
        
        return ids, uris

    @staticmethod
    async def _create_post(file_id: str, file_uri: str, token: str) -> Optional[str]:
        """Create video session"""
        try:
            result = await PostCreateManager.create(file_id, file_uri, token)
            if result and result.get("success"):
                return result.get("post_id")
        except Exception as e:
            logger.warning(f"[Client] Create session failed: {e}")
        return None

    @staticmethod
    def _build_payload(content: str, model: str, mode: str, img_ids: List[str], img_uris: List[str], is_video: bool = False, post_id: str = None) -> Dict:
        """Build request payload"""
        # 视频模型特殊处理
        if is_video and img_uris:
            img_msg = f"https://grok.com/imagine/{post_id}" if post_id else f"https://assets.grok.com/post/{img_uris[0]}"
            return {
                "temporary": True,
                "modelName": "grok-3",
                "message": f"{img_msg}  {content} --mode=custom",
                "fileAttachments": img_ids,
                "toolOverrides": {"videoGen": True}
            }
        
        # 标准载荷
        return {
            "temporary": setting.grok_config.get("temporary", True),
            "modelName": model,
            "message": content,
            "fileAttachments": img_ids,
            "imageAttachments": [],
            "disableSearch": False,
            "enableImageGeneration": True,
            "returnImageBytes": False,
            "returnRawGrokInXaiRequest": False,
            "enableImageStreaming": True,
            "imageGenerationCount": 2,
            "forceConcise": False,
            "toolOverrides": {},
            "enableSideBySide": True,
            "sendFinalMetadata": True,
            "isReasoning": False,
            "webpageUrls": [],
            "disableTextFollowUps": True,
            "responseMetadata": {"requestModelDetails": {"modelId": model}},
            "disableMemory": False,
            "forceSideBySide": False,
            "modelMode": mode,
            "isAsyncChat": False
        }

    @staticmethod
    async def _request(payload: dict, token: str, model: str, stream: bool, post_id: str = None):
        """Send request"""
        if not token:
            raise GrokApiException("Auth token missing", "NO_AUTH_TOKEN")

        # 外层重试：可配置状态码（401/429等）
        retry_codes = setting.grok_config.get("retry_status_codes", [401, 429])
        MAX_OUTER_RETRY = 3
        
        for outer_retry in range(MAX_OUTER_RETRY + 1):  # +1确保实际重试3次
            # 内层重试：403代理池重试
            max_403_retries = 5
            retry_403_count = 0
            
            while retry_403_count <= max_403_retries:
                try:
                    # 构建请求
                    headers = GrokClient._build_headers(token)
                    if model == "grok-imagine-0.9":
                        file_attachments = payload.get("fileAttachments", [])
                        ref_id = post_id or (file_attachments[0] if file_attachments else "")
                        if ref_id:
                            headers["Referer"] = f"https://grok.com/imagine/{ref_id}"
                    
                    # 异步获取代理
                    from app.core.proxy_pool import proxy_pool
                    
                    # 如果是403重试且使用代理池，强制刷新代理
                    if retry_403_count > 0 and proxy_pool._enabled:
                        logger.info(f"[Client] 403 retry {retry_403_count}/{max_403_retries}, refreshing proxy...")
                        proxy = await proxy_pool.force_refresh()
                    else:
                        proxy = await setting.get_proxy_async("service")
                    
                    proxies = {"http": proxy, "https": proxy} if proxy else None
                    
                    # 执行请求
                    response = await asyncio.to_thread(
                        curl_requests.post,
                        API_ENDPOINT,
                        headers=headers,
                        data=orjson.dumps(payload),
                        impersonate=BROWSER,
                        timeout=TIMEOUT,
                        stream=True,
                        proxies=proxies
                    )
                    
                    # 内层403重试：仅当有代理池时触发
                    if response.status_code == 403 and proxy_pool._enabled:
                        retry_403_count += 1
                        
                        if retry_403_count <= max_403_retries:
                            logger.warning(f"[Client] Encountered 403 error, retrying ({retry_403_count}/{max_403_retries})...")
                            await asyncio.sleep(0.5)
                            continue
                        
                        # 内层重试全部失败
                        logger.error(f"[Client] 403 error, retried {retry_403_count-1} times, giving up")
                    
                    # 检查可配置状态码错误 - 外层重试
                    if response.status_code in retry_codes:
                        if outer_retry < MAX_OUTER_RETRY:
                            delay = (outer_retry + 1) * 0.1  # 渐进延迟：0.1s, 0.2s, 0.3s
                            logger.warning(f"[Client] Encountered {response.status_code} error, outer retry ({outer_retry+1}/{MAX_OUTER_RETRY}), waiting {delay}s...")
                            await asyncio.sleep(delay)
                            break  # 跳出内层循环，进入外层重试
                        else:
                            logger.error(f"[Client] {response.status_code} error, retried {outer_retry} times, giving up")
                            GrokClient._handle_error(response, token)
                    
                    # 检查响应状态
                    if response.status_code != 200:
                        GrokClient._handle_error(response, token)
                    
                    # 成功 - 重置失败计数
                    asyncio.create_task(token_manager.reset_failure(token))
                    
                    # 如果是重试成功，记录日志
                    if outer_retry > 0 or retry_403_count > 0:
                        logger.info(f"[Client] Retry successful!")
                    
                    # 处理响应
                    result = (GrokResponseProcessor.process_stream(response, token) if stream 
                             else await GrokResponseProcessor.process_normal(response, token, model))
                    
                    asyncio.create_task(GrokClient._update_limits(token, model))
                    return result
                    
                except curl_requests.RequestsError as e:
                    logger.error(f"[Client] Network error: {e}")
                    raise GrokApiException(f"Network error: {e}", "NETWORK_ERROR") from e
                except GrokApiException:
                    # 重新抛出GrokApiException（包括403错误）
                    raise
                except Exception as e:
                    logger.error(f"[Client] Request error: {e}")
                    raise GrokApiException(f"Request error: {e}", "REQUEST_ERROR") from e
        
        # 理论上不应该到这里，但以防万一
        raise GrokApiException("Request failed: Max retries exceeded", "MAX_RETRIES_EXCEEDED")

    @staticmethod
    def _build_headers(token: str) -> Dict[str, str]:
        """Build request headers"""
        headers = get_dynamic_headers("/rest/app-chat/conversations/new")
        cf = setting.grok_config.get("cf_clearance", "")
        headers["Cookie"] = f"{token};{cf}" if cf else token
        return headers

    @staticmethod
    def _handle_error(response, token: str):
        """Handle error"""
        if response.status_code == 403:
            msg = "Your IP is blocked. Try one of: 1.Change IP 2.Use proxy 3.Configure CF value"
            data = {"cf_blocked": True, "status": 403}
            logger.warning(f"[Client] {msg}")
        else:
            try:
                data = response.json()
                msg = str(data)
            except:
                data = response.text
                msg = data[:200] if data else "Unknown error"
        
        asyncio.create_task(token_manager.record_failure(token, response.status_code, msg))
        raise GrokApiException(
            f"Request failed: {response.status_code} - {msg}",
            "HTTP_ERROR",
            {"status": response.status_code, "data": data}
        )

    @staticmethod
    async def _update_limits(token: str, model: str):
        """Update rate limits"""
        try:
            await token_manager.check_limits(token, model)
        except Exception as e:
            logger.error(f"[Client] Update limits failed: {e}")