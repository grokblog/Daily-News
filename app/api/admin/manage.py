"""管理接口 - Token管理和系统配置"""

import secrets
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.core.config import setting
from app.core.logger import logger
from app.services.grok.token import token_manager
from app.models.grok_models import TokenType


router = APIRouter(tags=["管理"])

# 常量
STATIC_DIR = Path(__file__).parents[2] / "template"
TEMP_DIR = Path(__file__).parents[3] / "data" / "temp"
IMAGE_CACHE_DIR = TEMP_DIR / "image"
VIDEO_CACHE_DIR = TEMP_DIR / "video"
SESSION_EXPIRE_HOURS = 24
BYTES_PER_KB = 1024
BYTES_PER_MB = 1024 * 1024

# 会话存储
_sessions: Dict[str, datetime] = {}


# === 请求/响应Model ===

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    message: str


class AddTokensRequest(BaseModel):
    tokens: List[str]
    token_type: str


class DeleteTokensRequest(BaseModel):
    tokens: List[str]
    token_type: str


class TokenInfo(BaseModel):
    token: str
    token_type: str
    created_time: Optional[int] = None
    remaining_queries: int
    heavy_remaining_queries: int
    status: str
    tags: List[str] = []
    note: str = ""


class TokenListResponse(BaseModel):
    success: bool
    data: List[TokenInfo]
    total: int


class UpdateSettingsRequest(BaseModel):
    global_config: Optional[Dict[str, Any]] = None
    grok_config: Optional[Dict[str, Any]] = None


class UpdateTokenTagsRequest(BaseModel):
    token: str
    token_type: str
    tags: List[str]


class UpdateTokenNoteRequest(BaseModel):
    token: str
    token_type: str
    note: str


class TestTokenRequest(BaseModel):
    token: str
    token_type: str


# === 辅助函数 ===

def validate_token_type(token_type_str: str) -> TokenType:
    """验证Token类型"""
    if token_type_str not in ["sso", "ssoSuper"]:
        raise HTTPException(
            status_code=400,
            detail={"error": "无效的Token类型", "code": "INVALID_TYPE"}
        )
    return TokenType.NORMAL if token_type_str == "sso" else TokenType.SUPER


def parse_created_time(created_time) -> Optional[int]:
    """解析创建时间"""
    if isinstance(created_time, str):
        return int(created_time) if created_time else None
    elif isinstance(created_time, int):
        return created_time
    return None


def calculate_token_stats(tokens: Dict[str, Any], token_type: str) -> Dict[str, int]:
    """计算Token统计"""
    total = len(tokens)
    expired = sum(1 for t in tokens.values() if t.get("status") == "expired")

    if token_type == "normal":
        unused = sum(1 for t in tokens.values()
                    if t.get("status") != "expired" and t.get("remainingQueries", -1) == -1)
        limited = sum(1 for t in tokens.values()
                     if t.get("status") != "expired" and t.get("remainingQueries", -1) == 0)
        active = sum(1 for t in tokens.values()
                    if t.get("status") != "expired" and t.get("remainingQueries", -1) > 0)
    else:
        unused = sum(1 for t in tokens.values()
                    if t.get("status") != "expired" and
                    t.get("remainingQueries", -1) == -1 and t.get("heavyremainingQueries", -1) == -1)
        limited = sum(1 for t in tokens.values()
                     if t.get("status") != "expired" and
                     (t.get("remainingQueries", -1) == 0 or t.get("heavyremainingQueries", -1) == 0))
        active = sum(1 for t in tokens.values()
                    if t.get("status") != "expired" and
                    (t.get("remainingQueries", -1) > 0 or t.get("heavyremainingQueries", -1) > 0))

    return {"total": total, "unused": unused, "limited": limited, "expired": expired, "active": active}


def verify_admin_session(authorization: Optional[str] = Header(None)) -> bool:
    """验证管理员会话"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"error": "未授权访问", "code": "UNAUTHORIZED"})
    
    token = authorization[7:]
    
    if token not in _sessions:
        raise HTTPException(status_code=401, detail={"error": "会话无效", "code": "SESSION_INVALID"})
    
    if datetime.now() > _sessions[token]:
        del _sessions[token]
        raise HTTPException(status_code=401, detail={"error": "会话已过期", "code": "SESSION_EXPIRED"})
    
    return True


def get_token_status(token_data: Dict[str, Any], token_type: str) -> str:
    """获取Token status"""
    if token_data.get("status") == "expired":
        return "Expired"
    
    remaining = token_data.get("remainingQueries", -1)
    heavy_remaining = token_data.get("heavyremainingQueries", -1)
    
    relevant = max(remaining, heavy_remaining) if token_type == "ssoSuper" else remaining
    
    if relevant == -1:
        return "未Using"
    elif relevant == 0:
        return "Rate Limited"
    else:
        return "Active"


def _calculate_dir_size(directory: Path) -> int:
    """计算目录大小"""
    total = 0
    for file_path in directory.iterdir():
        if file_path.is_file():
            try:
                total += file_path.stat().st_size
            except Exception as e:
                logger.warning(f"[Admin] Cannot get file size: {file_path.name}, {e}")
    return total


def _format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    size_mb = size_bytes / BYTES_PER_MB
    if size_mb < 1:
        return f"{size_bytes / BYTES_PER_KB:.1f} KB"
    return f"{size_mb:.1f} MB"


# === 页面路由 ===

@router.get("/login", response_class=HTMLResponse)
async def login_page():
    """登录页面"""
    login_html = STATIC_DIR / "login.html"
    if login_html.exists():
        return login_html.read_text(encoding="utf-8")
    raise HTTPException(status_code=404, detail="登录页面不存在")


@router.get("/manage", response_class=HTMLResponse)
async def manage_page():
    """管理页面"""
    admin_html = STATIC_DIR / "admin.html"
    if admin_html.exists():
        return admin_html.read_text(encoding="utf-8")
    raise HTTPException(status_code=404, detail="管理页面不存在")


# === API端点 ===

@router.post("/api/login", response_model=LoginResponse)
async def admin_login(request: LoginRequest) -> LoginResponse:
    """管理员登录"""
    try:
        logger.debug(f"[Admin] Login attempt: {request.username}")

        expected_user = setting.global_config.get("admin_username", "")
        expected_pass = setting.global_config.get("admin_password", "")

        if request.username != expected_user or request.password != expected_pass:
            logger.warning(f"[Admin] Login failed: {request.username}")
            return LoginResponse(success=False, message="用户名或密码errors")

        session_token = secrets.token_urlsafe(32)
        _sessions[session_token] = datetime.now() + timedelta(hours=SESSION_EXPIRE_HOURS)

        logger.debug(f"[Admin] Login successful: {request.username}")
        return LoginResponse(success=True, token=session_token, message="Login successful")

    except Exception as e:
        logger.error(f"[Admin] Login exception: {e}")
        raise HTTPException(status_code=500, detail={"error": f"Login failed: {e}", "code": "LOGIN_ERROR"})


@router.post("/api/logout")
async def admin_logout(_: bool = Depends(verify_admin_session), authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """管理员登出"""
    try:
        if authorization and authorization.startswith("Bearer "):
            token = authorization[7:]
            if token in _sessions:
                del _sessions[token]
                logger.debug("[Admin] Logout successful")
                return {"success": True, "message": "Logout successful"}

        logger.warning("[Admin] Logout failed: Invalid session")
        return {"success": False, "message": "无效的会话"}

    except Exception as e:
        logger.error(f"[Admin] Logout exception: {e}")
        raise HTTPException(status_code=500, detail={"error": f"Logout failed: {e}", "code": "LOGOUT_ERROR"})


@router.get("/api/tokens", response_model=TokenListResponse)
async def list_tokens(_: bool = Depends(verify_admin_session)) -> TokenListResponse:
    """Getting token list"""
    try:
        logger.debug("[Admin] Getting token list")

        all_tokens = token_manager.get_tokens()
        token_list: List[TokenInfo] = []

        # Normal tokens
        for token, data in all_tokens.get(TokenType.NORMAL.value, {}).items():
            token_list.append(TokenInfo(
                token=token,
                token_type="sso",
                created_time=parse_created_time(data.get("createdTime")),
                remaining_queries=data.get("remainingQueries", -1),
                heavy_remaining_queries=data.get("heavyremainingQueries", -1),
                status=get_token_status(data, "sso"),
                tags=data.get("tags", []),
                note=data.get("note", "")
            ))

        # Super Token
        for token, data in all_tokens.get(TokenType.SUPER.value, {}).items():
            token_list.append(TokenInfo(
                token=token,
                token_type="ssoSuper",
                created_time=parse_created_time(data.get("createdTime")),
                remaining_queries=data.get("remainingQueries", -1),
                heavy_remaining_queries=data.get("heavyremainingQueries", -1),
                status=get_token_status(data, "ssoSuper"),
                tags=data.get("tags", []),
                note=data.get("note", "")
            ))

        logger.debug(f"[Admin] Token list retrieved successfully: {len(token_list)}")
        return TokenListResponse(success=True, data=token_list, total=len(token_list))

    except Exception as e:
        logger.error(f"[Admin] Getting token listException: {e}")
        raise HTTPException(status_code=500, detail={"error": f"Failed to get: {e}", "code": "LIST_ERROR"})


@router.post("/api/tokens/add")
async def add_tokens(request: AddTokensRequest, _: bool = Depends(verify_admin_session)) -> Dict[str, Any]:
    """批量AddedToken"""
    try:
        logger.debug(f"[Admin] AddedToken: {request.token_type}, {len(request.tokens)}")

        token_type = validate_token_type(request.token_type)
        await token_manager.add_token(request.tokens, token_type)

        logger.debug(f"[Admin] Token added successfully: {len(request.tokens)}")
        return {"success": True, "message": f"成功Added {len(request.tokens)} Token", "count": len(request.tokens)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] TokenAddedException: {e}")
        raise HTTPException(status_code=500, detail={"error": f"AddedFailed: {e}", "code": "ADD_ERROR"})


@router.post("/api/tokens/delete")
async def delete_tokens(request: DeleteTokensRequest, _: bool = Depends(verify_admin_session)) -> Dict[str, Any]:
    """批量DeletedToken"""
    try:
        logger.debug(f"[Admin] DeletedToken: {request.token_type}, {len(request.tokens)}")

        token_type = validate_token_type(request.token_type)
        await token_manager.delete_token(request.tokens, token_type)

        logger.debug(f"[Admin] Token deleted successfully: {len(request.tokens)}")
        return {"success": True, "message": f"成功Deleted {len(request.tokens)} Token", "count": len(request.tokens)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] TokenDeletedException: {e}")
        raise HTTPException(status_code=500, detail={"error": f"DeletedFailed: {e}", "code": "DELETE_ERROR"})


@router.get("/api/settings")
async def get_settings(_: bool = Depends(verify_admin_session)) -> Dict[str, Any]:
    """Getting configuration"""
    try:
        logger.debug("[Admin] Getting configuration")
        return {"success": True, "data": {"global": setting.global_config, "grok": setting.grok_config}}
    except Exception as e:
        logger.error(f"[Admin] Getting configurationFailed: {e}")
        raise HTTPException(status_code=500, detail={"error": f"Failed to get: {e}", "code": "GET_SETTINGS_ERROR"})


@router.post("/api/settings")
async def update_settings(request: UpdateSettingsRequest, _: bool = Depends(verify_admin_session)) -> Dict[str, Any]:
    """Updating configuration"""
    try:
        logger.debug("[Admin] Updating configuration")
        await setting.save(global_config=request.global_config, grok_config=request.grok_config)
        logger.debug("[Admin] Configuration updated successfully")
        return {"success": True, "message": "Configuration updated successfully"}
    except Exception as e:
        logger.error(f"[Admin] Updating configurationFailed: {e}")
        raise HTTPException(status_code=500, detail={"error": f"更新Failed: {e}", "code": "UPDATE_SETTINGS_ERROR"})


@router.get("/api/cache/size")
async def get_cache_size(_: bool = Depends(verify_admin_session)) -> Dict[str, Any]:
    """Getting cache size"""
    try:
        logger.debug("[Admin] Getting cache size")

        image_size = _calculate_dir_size(IMAGE_CACHE_DIR) if IMAGE_CACHE_DIR.exists() else 0
        video_size = _calculate_dir_size(VIDEO_CACHE_DIR) if VIDEO_CACHE_DIR.exists() else 0
        total_size = image_size + video_size

        logger.debug(f"[Admin] Cache size: Image{_format_size(image_size)}, Video{_format_size(video_size)}")
        
        return {
            "success": True,
            "data": {
                "image_size": _format_size(image_size),
                "video_size": _format_size(video_size),
                "total_size": _format_size(total_size),
                "image_size_bytes": image_size,
                "video_size_bytes": video_size,
                "total_size_bytes": total_size
            }
        }

    except Exception as e:
        logger.error(f"[Admin] Getting cache sizeException: {e}")
        raise HTTPException(status_code=500, detail={"error": f"Failed to get: {e}", "code": "CACHE_SIZE_ERROR"})


@router.post("/api/cache/clear")
async def clear_cache(_: bool = Depends(verify_admin_session)) -> Dict[str, Any]:
    """清理所有缓存"""
    try:
        logger.debug("[Admin] Clearing cache")

        image_count = 0
        video_count = 0

        # 清理Image
        if IMAGE_CACHE_DIR.exists():
            for file_path in IMAGE_CACHE_DIR.iterdir():
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        image_count += 1
                    except Exception as e:
                        logger.error(f"[Admin] DeletedFailed: {file_path.name}, {e}")

        # 清理Video
        if VIDEO_CACHE_DIR.exists():
            for file_path in VIDEO_CACHE_DIR.iterdir():
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        video_count += 1
                    except Exception as e:
                        logger.error(f"[Admin] DeletedFailed: {file_path.name}, {e}")

        total = image_count + video_count
        logger.debug(f"[Admin] Cache cleanup complete: Image{image_count}, Video{video_count}")

        return {
            "success": True,
            "message": f"成功Clearing cache，DeletedImage {image_count} ，Video {video_count} ，共 {total} 文件",
            "data": {"deleted_count": total, "image_count": image_count, "video_count": video_count}
        }

    except Exception as e:
        logger.error(f"[Admin] Clearing cacheException: {e}")
        raise HTTPException(status_code=500, detail={"error": f"Cleanup failed: {e}", "code": "CACHE_CLEAR_ERROR"})


@router.post("/api/cache/clear/images")
async def clear_image_cache(_: bool = Depends(verify_admin_session)) -> Dict[str, Any]:
    """Clearing image cache"""
    try:
        logger.debug("[Admin] Clearing image cache")

        count = 0
        if IMAGE_CACHE_DIR.exists():
            for file_path in IMAGE_CACHE_DIR.iterdir():
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        count += 1
                    except Exception as e:
                        logger.error(f"[Admin] DeletedFailed: {file_path.name}, {e}")

        logger.debug(f"[Admin] ImageCache cleanup complete: {count}")
        return {"success": True, "message": f"成功Clearing image cache，Deleted {count} 文件", "data": {"deleted_count": count, "type": "images"}}

    except Exception as e:
        logger.error(f"[Admin] Clearing image cacheException: {e}")
        raise HTTPException(status_code=500, detail={"error": f"Cleanup failed: {e}", "code": "IMAGE_CACHE_CLEAR_ERROR"})


@router.post("/api/cache/clear/videos")
async def clear_video_cache(_: bool = Depends(verify_admin_session)) -> Dict[str, Any]:
    """Clearing video cache"""
    try:
        logger.debug("[Admin] Clearing video cache")

        count = 0
        if VIDEO_CACHE_DIR.exists():
            for file_path in VIDEO_CACHE_DIR.iterdir():
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        count += 1
                    except Exception as e:
                        logger.error(f"[Admin] DeletedFailed: {file_path.name}, {e}")

        logger.debug(f"[Admin] VideoCache cleanup complete: {count}")
        return {"success": True, "message": f"成功Clearing video cache，Deleted {count} 文件", "data": {"deleted_count": count, "type": "videos"}}

    except Exception as e:
        logger.error(f"[Admin] Clearing video cacheException: {e}")
        raise HTTPException(status_code=500, detail={"error": f"Cleanup failed: {e}", "code": "VIDEO_CACHE_CLEAR_ERROR"})


@router.get("/api/stats")
async def get_stats(_: bool = Depends(verify_admin_session)) -> Dict[str, Any]:
    """获取统计信息"""
    try:
        logger.debug("[Admin] Getting statistics")

        all_tokens = token_manager.get_tokens()
        normal_stats = calculate_token_stats(all_tokens.get(TokenType.NORMAL.value, {}), "normal")
        super_stats = calculate_token_stats(all_tokens.get(TokenType.SUPER.value, {}), "super")
        total = normal_stats["total"] + super_stats["total"]

        logger.debug(f"[Admin] Statistics retrieved successfully - Normal tokens: {normal_stats['total']}, Super Token: {super_stats['total']}, Total: {total}")
        return {"success": True, "data": {"normal": normal_stats, "super": super_stats, "total": total}}

    except Exception as e:
        logger.error(f"[Admin] Exception getting statistics: {e}")
        raise HTTPException(status_code=500, detail={"error": f"Failed to get: {e}", "code": "STATS_ERROR"})


@router.get("/api/storage/mode")
async def get_storage_mode(_: bool = Depends(verify_admin_session)) -> Dict[str, Any]:
    """Getting storage mode"""
    try:
        logger.debug("[Admin] Getting storage mode")
        import os
        mode = os.getenv("STORAGE_MODE", "file").upper()
        return {"success": True, "data": {"mode": mode}}
    except Exception as e:
        logger.error(f"[Admin] Getting storage modeException: {e}")
        raise HTTPException(status_code=500, detail={"error": f"Failed to get: {e}", "code": "STORAGE_MODE_ERROR"})


@router.post("/api/tokens/tags")
async def update_token_tags(request: UpdateTokenTagsRequest, _: bool = Depends(verify_admin_session)) -> Dict[str, Any]:
    """Updating token tags"""
    try:
        logger.debug(f"[Admin] Updating token tags: {request.token[:10]}..., {request.tags}")

        token_type = validate_token_type(request.token_type)
        await token_manager.update_token_tags(request.token, token_type, request.tags)

        logger.debug(f"[Admin] Token tags updated successfully: {request.token[:10]}...")
        return {"success": True, "message": "标签更新成功", "tags": request.tags}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] Exception updating token tags: {e}")
        raise HTTPException(status_code=500, detail={"error": f"更新Failed: {e}", "code": "UPDATE_TAGS_ERROR"})


@router.get("/api/tokens/tags/all")
async def get_all_tags(_: bool = Depends(verify_admin_session)) -> Dict[str, Any]:
    """Getting all tags"""
    try:
        logger.debug("[Admin] Getting all tags")

        all_tokens = token_manager.get_tokens()
        tags_set = set()

        for token_type_data in all_tokens.values():
            for token_data in token_type_data.values():
                tags = token_data.get("tags", [])
                if isinstance(tags, list):
                    tags_set.update(tags)

        tags_list = sorted(list(tags_set))
        logger.debug(f"[Admin] Tags retrieved successfully: {len(tags_list)}")
        return {"success": True, "data": tags_list}

    except Exception as e:
        logger.error(f"[Admin] Exception getting tags: {e}")
        raise HTTPException(status_code=500, detail={"error": f"Failed to get: {e}", "code": "GET_TAGS_ERROR"})


@router.post("/api/tokens/note")
async def update_token_note(request: UpdateTokenNoteRequest, _: bool = Depends(verify_admin_session)) -> Dict[str, Any]:
    """Updating token note"""
    try:
        logger.debug(f"[Admin] Updating token note: {request.token[:10]}...")

        token_type = validate_token_type(request.token_type)
        await token_manager.update_token_note(request.token, token_type, request.note)

        logger.debug(f"[Admin] Token note updated successfully: {request.token[:10]}...")
        return {"success": True, "message": "备注更新成功", "note": request.note}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] Exception updating token note: {e}")
        raise HTTPException(status_code=500, detail={"error": f"更新Failed: {e}", "code": "UPDATE_NOTE_ERROR"})


@router.post("/api/tokens/test")
async def test_token(request: TestTokenRequest, _: bool = Depends(verify_admin_session)) -> Dict[str, Any]:
    """Testing token可用性"""
    try:
        logger.debug(f"[Admin] Testing token: {request.token[:10]}...")

        token_type = validate_token_type(request.token_type)
        auth_token = f"sso-rw={request.token};sso={request.token}"

        result = await token_manager.check_limits(auth_token, "grok-4-fast")

        if result:
            logger.debug(f"[Admin] Token test successful: {request.token[:10]}...")
            return {
                "success": True,
                "message": "Token有效",
                "data": {
                    "valid": True,
                    "remaining_queries": result.get("remainingTokens", -1),
                    "limit": result.get("limit", -1)
                }
            }
        else:
            logger.warning(f"[Admin] Token test failed: {request.token[:10]}...")

            all_tokens = token_manager.get_tokens()
            token_data = all_tokens.get(token_type.value, {}).get(request.token)

            if token_data:
                if token_data.get("status") == "expired":
                    return {"success": False, "message": "Token expired", "data": {"valid": False, "error_type": "expired", "error_code": 401}}
                elif token_data.get("remainingQueries") == 0:
                    return {"success": False, "message": "Token is rate limited", "data": {"valid": False, "error_type": "limited", "error_code": "other"}}
                else:
                    return {"success": False, "message": "服务器被block或网络errors", "data": {"valid": False, "error_type": "blocked", "error_code": 403}}
            else:
                return {"success": False, "message": "Token数据Exception", "data": {"valid": False, "error_type": "unknown", "error_code": "data_error"}}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] Exception testing token: {e}")
        raise HTTPException(status_code=500, detail={"error": f"测试Failed: {e}", "code": "TEST_TOKEN_ERROR"})
