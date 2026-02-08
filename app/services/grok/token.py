"""Grok Token 管理器 - 单例模式的Token负载均衡和 status管理"""

import orjson
import time
import asyncio
import aiofiles
import portalocker
from pathlib import Path
from curl_cffi.requests import AsyncSession
from typing import Dict, Any, Optional, Tuple

from app.models.grok_models import TokenType, Models
from app.core.exception import GrokApiException
from app.core.logger import logger
from app.core.config import setting
from app.services.grok.statsig import get_dynamic_headers


# 常量
RATE_LIMIT_API = "https://grok.com/rest/rate-limits"
TIMEOUT = 30
BROWSER = "chrome133a"
MAX_FAILURES = 3
TOKEN_INVALID = 401
STATSIG_INVALID = 403


class GrokTokenManager:
    """Token管理器（单例）"""
    
    _instance: Optional['GrokTokenManager'] = None
    _lock = asyncio.Lock()

    def __new__(cls) -> 'GrokTokenManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self.token_file = Path(__file__).parents[3] / "data" / "token.json"
        self._file_lock = asyncio.Lock()
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        self._storage = None
        self.token_data = None  # 延迟Loading
        
        # 批量Saving队列
        self._save_pending = False  # 标记是否有待Saving的数据
        self._save_task = None  # 后台Saving任务
        self._shutdown = False  # 关闭标志
        
        # Video ID to Token mapping (for upscale)
        self._video_token_map: Dict[str, Dict[str, Any]] = {}  # {video_id: {token: str, timestamp: int}}
        self._video_map_max_age = 3600  # 1 hour expiry
        
        self._initialized = True
        logger.debug(f"[Token] Initialization complete: {self.token_file}")

    def set_storage(self, storage) -> None:
        """设置存储实例"""
        self._storage = storage

    async def _load_data(self) -> None:
        """异步LoadingToken数据（支持多进程）"""
        default = {TokenType.NORMAL.value: {}, TokenType.SUPER.value: {}}
        
        try:
            if self.token_file.exists():
                # 使用进程锁读取文件
                async with self._file_lock:
                    with open(self.token_file, "r", encoding="utf-8") as f:
                        portalocker.lock(f, portalocker.LOCK_SH)  # 共享锁（读）
                        try:
                            content = f.read()
                            self.token_data = orjson.loads(content)
                        finally:
                            portalocker.unlock(f)
            else:
                self.token_data = default
                logger.debug("[Token] Creating new data file")
        except Exception as e:
            logger.error(f"[Token] Failed to load: {e}")
            self.token_data = default

    async def _save_data(self) -> None:
        """SavingToken数据（支持多进程）"""
        try:
            if not self._storage:
                async with self._file_lock:
                    # 使用进程锁写入文件
                    with open(self.token_file, "w", encoding="utf-8") as f:
                        portalocker.lock(f, portalocker.LOCK_EX)  # 独占锁（写）
                        try:
                            content = orjson.dumps(self.token_data, option=orjson.OPT_INDENT_2).decode()
                            f.write(content)
                            f.flush()  # 确保写入磁盘
                        finally:
                            portalocker.unlock(f)
            else:
                await self._storage.save_tokens(self.token_data)
        except IOError as e:
            logger.error(f"[Token] Failed to save: {e}")
            raise GrokApiException(f"Failed to save: {e}", "TOKEN_SAVE_ERROR", {"file": str(self.token_file)})

    def _mark_dirty(self) -> None:
        """标记有待Saving的数据"""
        self._save_pending = True

    async def _batch_save_worker(self) -> None:
        """批量Saving后台任务"""
        from app.core.config import setting
        
        interval = setting.global_config.get("batch_save_interval", 1.0)
        logger.info(f"[Token] Storage task started, interval: {interval}s")
        
        while not self._shutdown:
            await asyncio.sleep(interval)
            
            if self._save_pending and not self._shutdown:
                try:
                    await self._save_data()
                    self._save_pending = False
                    logger.debug("[Token] Storage complete")
                except Exception as e:
                    logger.error(f"[Token] Storage failed: {e}")

    async def start_batch_save(self) -> None:
        """启动批量Saving任务"""
        if self._save_task is None:
            self._save_task = asyncio.create_task(self._batch_save_worker())
            logger.info("[Token] Storage task created")

    async def shutdown(self) -> None:
        """关闭并刷新所有待Saving数据"""
        self._shutdown = True
        
        if self._save_task:
            self._save_task.cancel()
            try:
                await self._save_task
            except asyncio.CancelledError:
                pass
        
        # 最终刷新
        if self._save_pending:
            await self._save_data()
            logger.info("[Token] Flush complete on shutdown")

    @staticmethod
    def _extract_sso(auth_token: str) -> Optional[str]:
        """提取SSO值"""
        if "sso=" in auth_token:
            return auth_token.split("sso=")[1].split(";")[0]
        logger.warning("[Token] Cannot extract SSO value")
        return None

    def _find_token(self, sso: str) -> Tuple[Optional[str], Optional[Dict]]:
        """查找Token"""
        for token_type in [TokenType.NORMAL.value, TokenType.SUPER.value]:
            if sso in self.token_data[token_type]:
                return token_type, self.token_data[token_type][sso]
        return None, None

    async def add_token(self, tokens: list[str], token_type: TokenType) -> None:
        """AddedToken"""
        if not tokens:
            return

        count = 0
        for token in tokens:
            if not token or not token.strip():
                continue

            self.token_data[token_type.value][token] = {
                "createdTime": int(time.time() * 1000),
                "remainingQueries": -1,
                "heavyremainingQueries": -1,
                "status": "active",
                "failedCount": 0,
                "lastFailureTime": None,
                "lastFailureReason": None,
                "tags": [],
                "note": ""
            }
            count += 1

        self._mark_dirty()  # 批量Saving
        logger.info(f"[Token] Added {count}  {token_type.value} Token")

    async def delete_token(self, tokens: list[str], token_type: TokenType) -> None:
        """DeletedToken"""
        if not tokens:
            return

        count = 0
        for token in tokens:
            if token in self.token_data[token_type.value]:
                del self.token_data[token_type.value][token]
                count += 1

        self._mark_dirty()  # 批量Saving
        logger.info(f"[Token] Deleted {count}  {token_type.value} Token")

    async def update_token_tags(self, token: str, token_type: TokenType, tags: list[str]) -> None:
        """更新Token标签"""
        if token not in self.token_data[token_type.value]:
            raise GrokApiException("Token不存在", "TOKEN_NOT_FOUND", {"token": token[:10]})
        
        cleaned = [t.strip() for t in tags if t and t.strip()]
        self.token_data[token_type.value][token]["tags"] = cleaned
        self._mark_dirty()  # 批量Saving
        logger.info(f"[Token] Updated tags: {token[:10]}... -> {cleaned}")

    async def update_token_note(self, token: str, token_type: TokenType, note: str) -> None:
        """更新Token备注"""
        if token not in self.token_data[token_type.value]:
            raise GrokApiException("Token不存在", "TOKEN_NOT_FOUND", {"token": token[:10]})
        
        self.token_data[token_type.value][token]["note"] = note.strip()
        self._mark_dirty()  # 批量Saving
        logger.info(f"[Token] Updated note: {token[:10]}...")
    
    def get_tokens(self) -> Dict[str, Any]:
        """获取所有Token"""
        return self.token_data.copy()

    def _reload_if_needed(self) -> None:
        """在多进程模式下重新Loading数据（同步版本，用于select_token）"""
        # 只在文件模式且多进程环境下才重新Loading
        if self._storage:
            return  # Database模式不需要
        
        try:
            if self.token_file.exists():
                with open(self.token_file, "r", encoding="utf-8") as f:
                    portalocker.lock(f, portalocker.LOCK_SH)
                    try:
                        content = f.read()
                        self.token_data = orjson.loads(content)
                    finally:
                        portalocker.unlock(f)
        except Exception as e:
            logger.warning(f"[Token] Reload failed: {e}")

    def get_token(self, model: str) -> str:
        """获取Token"""
        jwt = self.select_token(model)
        return f"sso-rw={jwt};sso={jwt}"
    
    def select_token(self, model: str) -> str:
        """选择最优Token（多进程安全）"""
        # 重新Loading最新数据（多进程模式）
        self._reload_if_needed()
        def select_best(tokens: Dict[str, Any], field: str) -> Tuple[Optional[str], Optional[int]]:
            """选择最佳Token"""
            unused, used = [], []

            for key, data in tokens.items():
                # Skip expired token
                if data.get("status") == "expired":
                    continue
                
                # 跳过Failed times数过多的token（任何errors status码）
                if data.get("failedCount", 0) >= MAX_FAILURES:
                    continue

                remaining = int(data.get(field, -1))
                if remaining == 0:
                    continue

                if remaining == -1:
                    unused.append(key)
                elif remaining > 0:
                    used.append((key, remaining))

            if unused:
                return unused[0], -1
            if used:
                used.sort(key=lambda x: x[1], reverse=True)
                return used[0][0], used[0][1]
            return None, None

        # 快照
        snapshot = {
            TokenType.NORMAL.value: self.token_data[TokenType.NORMAL.value].copy(),
            TokenType.SUPER.value: self.token_data[TokenType.SUPER.value].copy()
        }

        # 选择策略
        if model == "grok-4-heavy":
            field = "heavyremainingQueries"
            token_key, remaining = select_best(snapshot[TokenType.SUPER.value], field)
        else:
            field = "remainingQueries"
            token_key, remaining = select_best(snapshot[TokenType.NORMAL.value], field)
            if token_key is None:
                token_key, remaining = select_best(snapshot[TokenType.SUPER.value], field)

        if token_key is None:
            raise GrokApiException(
                f"没有可用Token: {model}",
                "NO_AVAILABLE_TOKEN",
                {
                    "model": model,
                    "normal": len(snapshot[TokenType.NORMAL.value]),
                    "super": len(snapshot[TokenType.SUPER.value])
                }
            )

        status = "Unused" if remaining == -1 else f"Remaining {remaining} times"
        logger.debug(f"[Token] Allocated token: {model} ({status})")
        return token_key
    
    async def check_limits(self, auth_token: str, model: str) -> Optional[Dict[str, Any]]:
        """检查速率限制"""
        try:
            rate_model = Models.to_rate_limit(model)
            payload = {"requestKind": "DEFAULT", "modelName": rate_model}
            
            cf = setting.grok_config.get("cf_clearance", "")
            headers = get_dynamic_headers("/rest/rate-limits")
            headers["Cookie"] = f"{auth_token};{cf}" if cf else auth_token

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
                        logger.info(f"[Token] 403 retry {retry_403_count}/{max_403_retries}，Refreshing proxy...")
                        proxy = await proxy_pool.force_refresh()
                    else:
                        proxy = await setting.get_proxy_async("service")
                    
                    proxies = {"http": proxy, "https": proxy} if proxy else None
                    
                    async with AsyncSession() as session:
                        response = await session.post(
                            RATE_LIMIT_API,
                            headers=headers,
                            json=payload,
                            impersonate=BROWSER,
                            timeout=TIMEOUT,
                            proxies=proxies
                        )

                        # 内层403 retry：仅当有代理池时触发
                        if response.status_code == 403 and proxy_pool._enabled:
                            retry_403_count += 1
                            
                            if retry_403_count <= max_403_retries:
                                logger.warning(f"[Token] Encountered 403 error, retrying ({retry_403_count}/{max_403_retries})...")
                                await asyncio.sleep(0.5)
                                continue
                            
                            # 内层重试全部Failed
                            logger.error(f"[Token] 403 error, retried{retry_403_count-1}times, giving up")
                            sso = self._extract_sso(auth_token)
                            if sso:
                                await self.record_failure(auth_token, 403, "服务器被Block")
                        
                        # 检查可配置 status码errors - outer retry
                        if response.status_code in retry_codes:
                            if outer_retry < MAX_OUTER_RETRY:
                                delay = (outer_retry + 1) * 0.1  # 渐进延迟：0.1s, 0.2s, 0.3s
                                logger.warning(f"[Token] Encountered{response.status_code}error, outer retry ({outer_retry+1}/{MAX_OUTER_RETRY})，waiting{delay}s...")
                                await asyncio.sleep(delay)
                                break  # 跳出内层循环，进入outer retry
                            else:
                                logger.error(f"[Token] {response.status_code}error, retried{outer_retry}times, giving up")
                                sso = self._extract_sso(auth_token)
                                if sso:
                                    if response.status_code == 401:
                                        await self.record_failure(auth_token, 401, "Token expired")
                                    else:
                                        await self.record_failure(auth_token, response.status_code, f"errors: {response.status_code}")
                                return None

                        if response.status_code == 200:
                            data = response.json()
                            sso = self._extract_sso(auth_token)
                            
                            if outer_retry > 0 or retry_403_count > 0:
                                logger.info(f"[Token] Retry successful!")
                            
                            if sso:
                                if model == "grok-4-heavy":
                                    await self.update_limits(sso, normal=None, heavy=data.get("remainingQueries", -1))
                                    logger.info(f"[Token] Updated limits: {sso[:10]}..., heavy={data.get('remainingQueries', -1)}")
                                else:
                                    await self.update_limits(sso, normal=data.get("remainingTokens", -1), heavy=None)
                                    logger.info(f"[Token] Updated limits: {sso[:10]}..., basic={data.get('remainingTokens', -1)}")
                            
                            return data
                        else:
                            # 其他errors
                            logger.warning(f"[Token] Failed to get limits: {response.status_code}")
                            sso = self._extract_sso(auth_token)
                            if sso:
                                await self.record_failure(auth_token, response.status_code, f"errors: {response.status_code}")
                            return None

        except Exception as e:
            logger.error(f"[Token] Error checking limits: {e}")
            return None

    async def update_limits(self, sso: str, normal: Optional[int] = None, heavy: Optional[int] = None) -> None:
        """Updated limits"""
        try:
            for token_type in [TokenType.NORMAL.value, TokenType.SUPER.value]:
                if sso in self.token_data[token_type]:
                    if normal is not None:
                        self.token_data[token_type][sso]["remainingQueries"] = normal
                    if heavy is not None:
                        self.token_data[token_type][sso]["heavyremainingQueries"] = heavy
                    self._mark_dirty()  # 批量Saving
                    logger.info(f"[Token] Updated limits: {sso[:10]}...")
                    return
            logger.warning(f"[Token] Not found: {sso[:10]}...")
        except Exception as e:
            logger.error(f"[Token] Updated limitserrors: {e}")
    
    async def record_failure(self, auth_token: str, status: int, msg: str) -> None:
        """记录Failed"""
        try:
            if status == STATSIG_INVALID:
                logger.warning("[Token] IP blocked. Try: 1.Change IP 2.Use proxy 3.Configure CF value")
                return

            sso = self._extract_sso(auth_token)
            if not sso:
                return

            _, data = self._find_token(sso)
            if not data:
                logger.warning(f"[Token] Not found: {sso[:10]}...")
                return

            data["failedCount"] = data.get("failedCount", 0) + 1
            data["lastFailureTime"] = int(time.time() * 1000)
            data["lastFailureReason"] = f"{status}: {msg}"

            logger.warning(
                f"[Token] Failed: {sso[:10]}... ( status:{status}), "
                f" times数: {data['failedCount']}/{MAX_FAILURES}, 原因: {msg}"
            )

            if 400 <= status < 500 and data["failedCount"] >= MAX_FAILURES:
                data["status"] = "expired"
                logger.error(f"[Token] Marked as invalid: {sso[:10]}... (consecutive{status}errors{data['failedCount']} times)")

            self._mark_dirty()  # 批量Saving

        except Exception as e:
            logger.error(f"[Token] Error recording failure: {e}")

    async def reset_failure(self, auth_token: str) -> None:
        """Reset failure count"""
        try:
            sso = self._extract_sso(auth_token)
            if not sso:
                return

            _, data = self._find_token(sso)
            if not data:
                return

            if data.get("failedCount", 0) > 0:
                data["failedCount"] = 0
                data["lastFailureTime"] = None
                data["lastFailureReason"] = None
                self._mark_dirty()  # 批量Saving
                logger.info(f"[Token] Reset failure count: {sso[:10]}...")

        except Exception as e:
            logger.error(f"[Token] Error resetting failure: {e}")

    def register_video_token(self, video_id: str, auth_token: str) -> None:
        """Register video_id to token mapping for upscale"""
        try:
            # Clean up old entries first
            self._cleanup_video_map()
            
            # Store the mapping
            self._video_token_map[video_id] = {
                "token": auth_token,
                "timestamp": int(time.time())
            }
            logger.info(f"[Token] Registered video mapping: {video_id[:20]}... -> token")
        except Exception as e:
            logger.error(f"[Token] Error registering video token: {e}")

    def get_video_token(self, video_id: str) -> Optional[str]:
        """Get token associated with video_id for upscale"""
        try:
            if video_id in self._video_token_map:
                entry = self._video_token_map[video_id]
                # Check if not expired
                if int(time.time()) - entry["timestamp"] < self._video_map_max_age:
                    logger.info(f"[Token] Found token for video: {video_id[:20]}...")
                    return entry["token"]
                else:
                    # Expired, remove it
                    del self._video_token_map[video_id]
                    logger.debug(f"[Token] Video mapping expired: {video_id[:20]}...")
            
            logger.warning(f"[Token] No token mapping found for video: {video_id[:20]}...")
            return None
        except Exception as e:
            logger.error(f"[Token] Error getting video token: {e}")
            return None

    def _cleanup_video_map(self) -> None:
        """Remove expired video-token mappings"""
        try:
            current_time = int(time.time())
            expired_keys = [
                k for k, v in self._video_token_map.items()
                if current_time - v["timestamp"] > self._video_map_max_age
            ]
            for key in expired_keys:
                del self._video_token_map[key]
            if expired_keys:
                logger.debug(f"[Token] Cleaned up {len(expired_keys)} expired video mappings")
        except Exception as e:
            logger.error(f"[Token] Error cleaning video map: {e}")


# 全局实例
token_manager = GrokTokenManager()
