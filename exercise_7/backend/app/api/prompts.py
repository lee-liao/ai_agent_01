from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
import asyncio
import openai
import re

from app.services.prompt_store import (
    list_versions,
    create_version,
    set_deploy,
    resolve_prompt,
    log_prompt_call,
    get_version_stats,
    get_version_stats_limited,
    get_version,
    list_prompts,
    get_prompt,
    update_prompt_variables,
    delete_version,
    update_version,
    get_current_deployment,
)
from app.services.rag.llm_service import get_llm_service
from app.config import settings
from app.database import execute_raw_query  # Add this import

router = APIRouter(tags=["Prompts"])


# Most specific routes first
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


@router.post("/execute")
async def execute_prompt(body: Dict[str, Any]):
    """Execute a prompt with given variables and return the LLM response"""
    prompt_id = body.get("prompt_id")
    env = body.get("env", "development")
    variables = body.get("variables", {})
    version = body.get("version")  # Optional version parameter for testing
    
    if not prompt_id:
        raise HTTPException(status_code=400, detail="prompt_id is required")
    
    # If version is specified, get that specific version, otherwise use resolve_prompt
    if version:
        # Get specific version directly
        version_details = await get_version(prompt_id, version)
        if not version_details:
            raise HTTPException(status_code=404, detail=f"Version {version} not found for prompt {prompt_id}")
        
        # Get the prompt version ID for logging
        version_rows = await execute_raw_query(
            "SELECT id FROM prompt_versions WHERE prompt_id=$1 AND version=$2",
            prompt_id,
            version
        )
        if not version_rows:
            raise HTTPException(status_code=404, detail=f"Version {version} not found for prompt {prompt_id}")
        
        prompt_version_id = version_rows[0]["id"]
        resolved = {
            "prompt_id": prompt_id,
            "version": version,
            "template": version_details["template"],
            "metadata": version_details["metadata"],
            "prompt_version_id": prompt_version_id
        }
    else:
        # Resolve the prompt to get the template (follows A/B testing logic)
        resolved = await resolve_prompt(f"prompt://{prompt_id}", env)
    
    if not resolved or not resolved.get("template"):
        raise HTTPException(status_code=404, detail="Prompt not found or has no template")
    
    template = resolved["template"]
    
    # Parse template to extract system and user parts
    system_match = re.search(r"System:\s*(.+?)(?=\s*Inputs:|$)", template, re.IGNORECASE | re.DOTALL)
    inputs_match = re.search(r"Inputs:\s*(.+)", template, re.IGNORECASE | re.DOTALL)
    
    system_prompt = system_match.group(1).strip() if system_match else ""
    user_prompt = inputs_match.group(1).strip() if inputs_match else ""
    
    # Replace variables in the user prompt
    for key, value in variables.items():
        user_prompt = user_prompt.replace(f"{{{key}}}", str(value))
    
    # Get LLM service
    llm_service = get_llm_service()
    if not llm_service:
        raise HTTPException(status_code=503, detail="LLM service not available")
    
    try:
        # Generate response using LLM
        def generate_sync():
            return llm_service.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=settings.openai_temperature,
                max_tokens=min(settings.openai_max_tokens, 500),
                timeout=30.0
            )
        
        response = await asyncio.get_event_loop().run_in_executor(None, generate_sync)
        response_text = response.choices[0].message.content
        
        # Calculate approximate cost (simplified)
        # In a real implementation, you would use the actual token counts from the response
        prompt_tokens = len(system_prompt + user_prompt) // 4  # Rough estimation
        completion_tokens = len(response_text) // 4  # Rough estimation
        cost = (prompt_tokens * 0.0000005 + completion_tokens * 0.0000015)  # GPT-4 pricing approximation
        
        # Log the call
        await log_prompt_call(resolved["prompt_version_id"], True, cost)
        
        return {
            "response": response_text,
            "cost": cost,
            "prompt_version_id": resolved["prompt_version_id"],
            "model": settings.openai_model
        }
        
    except Exception as e:
        # Log failed call
        await log_prompt_call(resolved["prompt_version_id"], False, 0.0)
        raise HTTPException(status_code=500, detail=f"Error calling LLM: {str(e)}")


# Routes with prompt_id parameter (more specific)
@router.get("/{prompt_id}/current-deployment")
async def get_current_deployment_endpoint(prompt_id: str, env: str = "development"):
    deployment = await get_current_deployment(env, prompt_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return deployment


@router.get("/{prompt_id}/versions")
async def get_versions_endpoint(prompt_id: str):
    return {"prompt_id": prompt_id, "versions": await list_versions(prompt_id)}


@router.get("/{prompt_id}/stats")
async def get_stats_endpoint(prompt_id: str):
    return {"prompt_id": prompt_id, "stats": await get_version_stats_limited(prompt_id)}


@router.get("/{prompt_id}/diff")
async def get_diff_endpoint(prompt_id: str, v1: int, v2: int):
    v1_details = await get_version(prompt_id, v1)
    v2_details = await get_version(prompt_id, v2)
    if not v1_details or not v2_details:
        raise HTTPException(status_code=404, detail="One or both versions not found")
    return {"v1": v1_details, "v2": v2_details}


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


@router.put("/{prompt_id}/versions/{version}")
async def update_prompt_version(prompt_id: str, version: int, body: Dict[str, Any]):
    """Update a specific version of a prompt"""
    template = body.get("template")
    changelog = body.get("changelog", "")
    if not template:
        raise HTTPException(status_code=400, detail="template is required")
    return await update_version(prompt_id, version, template, changelog)


@router.delete("/{prompt_id}/versions/{version}")
async def delete_prompt_version_endpoint(prompt_id: str, version: int):
    """Delete a specific version of a prompt"""
    try:
        await delete_version(prompt_id, version)
        return {"status": "ok", "message": f"Version {version} deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{prompt_id}")
async def get_prompt_endpoint(prompt_id: str):
    prompt = await get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


# Less specific routes last
@router.get("/")
async def list_prompts_endpoint():
    prompts = await list_prompts()
    return {"prompts": prompts}