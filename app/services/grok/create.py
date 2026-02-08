"""Post创建管理器 - 用于视频生成前的会话创建"""

import asyncio
import orjson
from typing import Dict, Any, Optional
from curl_cffi.requests import AsyncSession

from app.services.grok.statsig import get_dynamic_headers
from app.core.exception import GrokApiException
from app.core.config import setting
from app.core.logger import logger


# 常量
ENDPOINT = "https://grok.com/rest/media/post/create"
TIMEOUT = 30
BROWSER = "chrome133a"


class PostCreateManager:
    """会话创建管理器"""

    @staticmethod
    async def create(file_id: str, file_uri: str, auth_token: str) -> Optional[Dict[str, Any]]:
        """Creating session记录
        
        Args:
            file_id: 文件ID
            file_uri: 文件URI
            auth_token: 认证令牌
            
        Returns:
            会话信息字典，包含post_id等
        """
        # 参数验证
        if not file_id or not file_uri:
            raise GrokApiException("文件ID或URI缺失", "INVALID_PARAMS")
        if not auth_token:
            raise GrokApiException("认证令牌缺失", "NO_AUTH_TOKEN")

        try:
            # 构建请求
            data = {
                "media_url": f"https://assets.grok.com/{file_uri}",
                "media_type": "MEDIA_POST_TYPE_IMAGE"
            }
            
            cf = setting.grok_config.get("cf_clearance", "")
            headers = {
                **get_dynamic_headers("/rest/media/post/create"),
                "Cookie": f"{auth_token};{cf}" if cf else auth_token
            }
            
            # outer retry：可配置 status码（401/429等）
            retry_codes = setting.grok_config.get("retry_status_codes", [401, 429])
            MAX_OUTER_RETRY = 3
            
            for outer_retry in range(MAX_OUTER_RETRY + 1):  # +1 确保实际重试3 times
                # 内层重试：403代理池重试
                max_403_retries = 5
                retry_403_count = 0
                
                while retry_403_count <= max_403_retries:
                    # 异步获取代理（支持代理池）
                    from app.core.proxy_pool import proxy_pool
                    
                    # 如果是403 retry且使用代理池，Force refreshing proxy
                    if retry_403_count > 0 and proxy_pool._enabled:
                        logger.info(f"[PostCreate] 403 retry {retry_403_count}/{max_403_retries}，Refreshing proxy...")
                        proxy = await proxy_pool.force_refresh()
                    else:
                        proxy = await setting.get_proxy_async("service")
                    
                    proxies = {"http": proxy, "https": proxy} if proxy else None

                    # 发送请求
                    async with AsyncSession() as session:
                        response = await session.post(
                            ENDPOINT,
                            headers=headers,
                            json=data,
                            impersonate=BROWSER,
                            timeout=TIMEOUT,
                            proxies=proxies
                        )

                        # 内层403 retry：仅当有代理池时触发
                        if response.status_code == 403 and proxy_pool._enabled:
                            retry_403_count += 1
                            
                            if retry_403_count <= max_403_retries:
                                logger.warning(f"[PostCreate] Encountered 403 error, retrying ({retry_403_count}/{max_403_retries})...")
                                await asyncio.sleep(0.5)
                                continue
                            
                            # 内层重试全部Failed
                            logger.error(f"[PostCreate] 403 error, retried{retry_403_count-1}times, giving up")
                        
                        # 检查可配置 status码errors - outer retry
                        if response.status_code in retry_codes:
                            if outer_retry < MAX_OUTER_RETRY:
                                delay = (outer_retry + 1) * 0.1  # 渐进延迟：0.1s, 0.2s, 0.3s
                                logger.warning(f"[PostCreate] Encountered{response.status_code}error, outer retry ({outer_retry+1}/{MAX_OUTER_RETRY})，waiting{delay}s...")
                                await asyncio.sleep(delay)
                                break  # 跳出内层循环，进入outer retry
                            else:
                                logger.error(f"[PostCreate] {response.status_code}error, retried{outer_retry}times, giving up")
                                raise GrokApiException(f"创建Failed: {response.status_code}errors", "CREATE_ERROR")

                        if response.status_code == 200:
                            result = response.json()
                            post_id = result.get("post", {}).get("id", "")
                            
                            if outer_retry > 0 or retry_403_count > 0:
                                logger.info(f"[PostCreate] Retry successful!")
                            
                            logger.debug(f"[PostCreate] Success, session ID: {post_id}")
                            return {
                                "post_id": post_id,
                                "file_id": file_id,
                                "file_uri": file_uri,
                                "success": True,
                                "data": result
                            }
                        
                        # 其他errors处理
                        try:
                            error = response.json()
                            msg = f" status码: {response.status_code}, 详情: {error}"
                        except:
                            msg = f" status码: {response.status_code}, 详情: {response.text[:200]}"
                        
                        logger.error(f"[PostCreate] Failed: {msg}")
                        raise GrokApiException(f"创建Failed: {msg}", "CREATE_ERROR")

        except GrokApiException:
            raise
        except Exception as e:
            logger.error(f"[PostCreate] Exception: {e}")
            raise GrokApiException(f"创建Exception: {e}", "CREATE_ERROR") from e
