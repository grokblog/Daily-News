"""代理池管理器 - 从URL动态获取代理IP"""

import asyncio
import aiohttp
import time
from typing import Optional, List
from app.core.logger import logger


class ProxyPool:
    """代理池管理器"""
    
    def __init__(self):
        self._pool_url: Optional[str] = None
        self._static_proxy: Optional[str] = None
        self._current_proxy: Optional[str] = None
        self._last_fetch_time: float = 0
        self._fetch_interval: int = 300  # 5分钟刷新一 times
        self._enabled: bool = False
        self._lock = asyncio.Lock()
    
    def configure(self, proxy_url: str, proxy_pool_url: str = "", proxy_pool_interval: int = 300):
        """配置代理池
        
        Args:
            proxy_url: 静态代理URL（socks5h://xxx 或 http://xxx）
            proxy_pool_url: 代理池API URL，Returning单代理地址
            proxy_pool_interval: 代理池refresh interval（s）
        """
        self._static_proxy = self._normalize_proxy(proxy_url) if proxy_url else None
        pool_url = proxy_pool_url.strip() if proxy_pool_url else None
        if pool_url and self._looks_like_proxy_url(pool_url):
            normalized_proxy = self._normalize_proxy(pool_url)
            if not self._static_proxy:
                self._static_proxy = normalized_proxy
                logger.warning("[ProxyPool] proxy_pool_url looks like a proxy address, used as static proxy, please use proxy_url instead")
            else:
                logger.warning("[ProxyPool] proxy_pool_url looks like a proxy address, ignored (using proxy_url)")
            pool_url = None
        self._pool_url = pool_url
        self._fetch_interval = proxy_pool_interval
        self._enabled = bool(self._pool_url)
        
        if self._enabled:
            logger.info(f"[ProxyPool] Proxy pool enabled: {self._pool_url}, refresh interval: {self._fetch_interval}s")
        elif self._static_proxy:
            logger.info(f"[ProxyPool] Using static proxy: {self._static_proxy}")
            self._current_proxy = self._static_proxy
        else:
            logger.info("[ProxyPool] No proxy configured")
    
    async def get_proxy(self) -> Optional[str]:
        """获取代理地址
        
        Returns:
            代理URL或None
        """
        # 如果未启用代理池，Returning静态代理
        if not self._enabled:
            return self._static_proxy
        
        # 检查是否需要刷新
        now = time.time()
        if not self._current_proxy or (now - self._last_fetch_time) >= self._fetch_interval:
            async with self._lock:
                # 双重检查
                if not self._current_proxy or (now - self._last_fetch_time) >= self._fetch_interval:
                    await self._fetch_proxy()
        
        return self._current_proxy
    
    async def force_refresh(self) -> Optional[str]:
        """Force refreshing proxy（用于403errors重试）
        
        Returns:
            新的代理URL或None
        """
        if not self._enabled:
            return self._static_proxy
        
        async with self._lock:
            await self._fetch_proxy()
        
        return self._current_proxy
    
    async def _fetch_proxy(self):
        """从代理池URL获取新的代理"""
        try:
            logger.debug(f"[ProxyPool] Fetching new proxy from pool: {self._pool_url}")
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self._pool_url) as response:
                    if response.status == 200:
                        proxy_text = await response.text()
                        proxy = self._normalize_proxy(proxy_text.strip())
                        
                        # 验证代理格式
                        if self._validate_proxy(proxy):
                            self._current_proxy = proxy
                            self._last_fetch_time = time.time()
                            logger.info(f"[ProxyPool] Successfully got new proxy: {proxy}")
                        else:
                            logger.error(f"[ProxyPool] Invalid proxy format: {proxy}")
                            # 降级到静态代理
                            if not self._current_proxy:
                                self._current_proxy = self._static_proxy
                    else:
                        logger.error(f"[ProxyPool] Failed to get proxy: HTTP {response.status}")
                        # 降级到静态代理
                        if not self._current_proxy:
                            self._current_proxy = self._static_proxy
        
        except asyncio.TimeoutError:
            logger.error("[ProxyPool] Proxy fetch timeout")
            if not self._current_proxy:
                self._current_proxy = self._static_proxy
        
        except Exception as e:
            logger.error(f"[ProxyPool] Proxy fetch exception: {e}")
            # 降级到静态代理
            if not self._current_proxy:
                self._current_proxy = self._static_proxy
    
    def _validate_proxy(self, proxy: str) -> bool:
        """验证代理格式
        
        Args:
            proxy: 代理URL
        
        Returns:
            是否有效
        """
        if not proxy:
            return False
        
        # 支持的协议
        valid_protocols = ['http://', 'https://', 'socks5://', 'socks5h://']
        
        return any(proxy.startswith(proto) for proto in valid_protocols)

    def _normalize_proxy(self, proxy: str) -> str:
        """标准化代理URL（sock5/socks5 → socks5h://）"""
        if not proxy:
            return proxy

        proxy = proxy.strip()
        if proxy.startswith("sock5h://"):
            proxy = proxy.replace("sock5h://", "socks5h://", 1)
        if proxy.startswith("sock5://"):
            proxy = proxy.replace("sock5://", "socks5://", 1)
        if proxy.startswith("socks5://"):
            return proxy.replace("socks5://", "socks5h://", 1)
        return proxy

    def _looks_like_proxy_url(self, url: str) -> bool:
        """判断URL是否像代理地址（避免误把代理池API当代理）"""
        return url.startswith(("sock5://", "sock5h://", "socks5://", "socks5h://"))
    
    def get_current_proxy(self) -> Optional[str]:
        """获取当前Using的代理（同步方法）
        
        Returns:
            当前代理URL或None
        """
        return self._current_proxy or self._static_proxy


# 全局代理池实例
proxy_pool = ProxyPool()
