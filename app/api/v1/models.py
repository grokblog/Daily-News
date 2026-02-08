"""Model接口 - OpenAI兼容的Model列表端点"""

import time
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends

from app.models.grok_models import Models
from app.core.auth import auth_manager
from app.core.logger import logger


router = APIRouter(tags=["Model"])


@router.get("/models")
async def list_models(_: Optional[str] = Depends(auth_manager.verify)) -> Dict[str, Any]:
    """获取可用Model列表"""
    try:
        logger.debug("[Models] Requesting model list")

        timestamp = int(time.time())
        model_data: List[Dict[str, Any]] = []
        
        for model in Models:
            model_id = model.value
            config = Models.get_model_info(model_id)
            
            model_info = {
                "id": model_id,
                "object": "model", 
                "created": timestamp,
                "owned_by": "x-ai",
                "display_name": config.get("display_name", model_id),
                "description": config.get("description", ""),
                "raw_model_path": config.get("raw_model_path", f"xai/{model_id}"),
                "default_temperature": config.get("default_temperature", 1.0),
                "default_max_output_tokens": config.get("default_max_output_tokens", 8192),
                "supported_max_output_tokens": config.get("supported_max_output_tokens", 131072),
                "default_top_p": config.get("default_top_p", 0.95)
            }
            
            model_data.append(model_info)
        
        logger.debug(f"[Models] Returning {len(model_data)} Model")
        return {"object": "list", "data": model_data}
        
    except Exception as e:
        logger.error(f"[Models] Failed to get list: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": f"Failed to retrieve models: {e}",
                    "type": "internal_error",
                    "code": "model_list_error"
                }
            }
        )


@router.get("/models/{model_id}")
async def get_model(model_id: str, _: Optional[str] = Depends(auth_manager.verify)) -> Dict[str, Any]:
    """获取特定Model信息"""
    try:
        logger.debug(f"[Models] Requesting model: {model_id}")

        # 验证Model
        if not Models.is_valid_model(model_id):
            logger.warning(f"[Models] Model not found: {model_id}")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "message": f"Model '{model_id}' not found",
                        "type": "invalid_request_error", 
                        "code": "model_not_found"
                    }
                }
            )
        
        timestamp = int(time.time())
        config = Models.get_model_info(model_id)
        
        model_info = {
            "id": model_id,
            "object": "model",
            "created": timestamp,
            "owned_by": "x-ai",
            "display_name": config.get("display_name", model_id),
            "description": config.get("description", ""),
            "raw_model_path": config.get("raw_model_path", f"xai/{model_id}"),
            "default_temperature": config.get("default_temperature", 1.0),
            "default_max_output_tokens": config.get("default_max_output_tokens", 8192),
            "supported_max_output_tokens": config.get("supported_max_output_tokens", 131072),
            "default_top_p": config.get("default_top_p", 0.95)
        }

        logger.debug(f"[Models] ReturningModel: {model_id}")
        return model_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Models] Failed to get model: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": f"Failed to retrieve model: {e}",
                    "type": "internal_error",
                    "code": "model_retrieve_error"
                }
            }
        )
