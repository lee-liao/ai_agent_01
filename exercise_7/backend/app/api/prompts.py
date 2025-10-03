from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List

from app.services.prompt_store import (
    list_versions,
    create_version,
    set_deploy,
    resolve_prompt,
    log_prompt_call,
    get_version_stats,
    get_version,
    list_prompts,
    get_prompt,
    update_prompt_variables,
    delete_version,
    update_version,
)

router = APIRouter(tags=["Prompts"])


# More specific routes first
@router.get("/resolve")
async def resolve(prompt: str, env: str = "development", user_key: Optional[str] = None):
    return await resolve_prompt(prompt, env, user_key)


@router.post("/log_call")
async def log_call_endpoint(body: Dict[str, Any]):
    prompt_version_id = body.get("prompt_version_id")
    success = body.get("success")
    cost = body.get("cost")
    if not prompt_version_id or success is None or cost is None:
        raise HTTPException(status_code=400, detail="prompt_version_id, success, and cost are required")
    await log_prompt_call(prompt_version_id, success, cost)
    return {"status": "ok"}


# Routes with prompt_id parameter (more specific)
@router.get("/{prompt_id}/versions")
async def get_versions_endpoint(prompt_id: str):
    return {"prompt_id": prompt_id, "versions": await list_versions(prompt_id)}


@router.post("/{prompt_id}/deploy")
async def deploy_prompt(prompt_id: str, body: Dict[str, Any]):
    env = body.get("env", "development")
    strategy = body.get("strategy", "fixed")
    active_version = body.get("active_version")
    ab_alt_version = body.get("ab_alt_version")
    traffic_split = body.get("traffic_split", 0)
    if not active_version and strategy == "fixed":
        raise HTTPException(status_code=400, detail="active_version is required for fixed strategy")
    return await set_deploy(env, prompt_id, strategy, int(active_version or 1), ab_alt_version, int(traffic_split or 0))


@router.post("/{prompt_id}")
async def create_prompt_version(prompt_id: str, body: Dict[str, Any]):
    template = body.get("template")
    metadata = body.get("metadata", {})
    changelog = body.get("changelog", "")
    created_by = body.get("created_by", "user")
    if not template:
        raise HTTPException(status_code=400, detail="template is required")
    return await create_version(prompt_id, template, metadata, changelog, created_by)


@router.put("/{prompt_id}")
async def update_prompt_variables_endpoint(prompt_id: str, body: Dict[str, Any]):
    """Update prompt variables"""
    variables = body.get("variables", {})
    await update_prompt_variables(prompt_id, variables)
    return {"status": "ok", "message": "Prompt variables updated successfully"}


@router.get("/{prompt_id}/stats")
async def get_stats_endpoint(prompt_id: str):
    return {"prompt_id": prompt_id, "stats": await get_version_stats(prompt_id)}


@router.get("/{prompt_id}/diff")
async def get_diff_endpoint(prompt_id: str, v1: int, v2: int):
    v1_details = await get_version(prompt_id, v1)
    v2_details = await get_version(prompt_id, v2)
    if not v1_details or not v2_details:
        raise HTTPException(status_code=404, detail="One or both versions not found")
    return {"v1": v1_details, "v2": v2_details}


@router.put("/{prompt_id}/versions/{version}")
async def update_prompt_version(prompt_id: str, version: int, body: Dict[str, Any]):
    """Update a specific version of a prompt"""
    template = body.get("template")
    changelog = body.get("changelog", "")
    if not template:
        raise HTTPException(status_code=400, detail="template is required")
    return await update_version(prompt_id, version, template, changelog)


@router.delete("/{prompt_id}/versions/{version}")
async def delete_prompt_version(prompt_id: str, version: int):
    """Delete a specific version of a prompt"""
    try:
        result = await delete_version(prompt_id, version)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{prompt_id}/current-deployment")
async def get_current_deployment_endpoint(prompt_id: str, env: str = "development"):
    """Get current deployment information for a prompt"""
    from app.services.prompt_store import get_current_deployment
    deployment = await get_current_deployment(env, prompt_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return deployment


# General routes last
@router.get("/{prompt_id}")
async def get_prompt_endpoint(prompt_id: str):
    """Get a specific prompt"""
    prompt = await get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.get("/")
async def list_prompts_endpoint() -> Dict[str, List[Dict[str, Any]]]:
    """Get all available prompts"""
    prompts = await list_prompts()
    return {"prompts": prompts}