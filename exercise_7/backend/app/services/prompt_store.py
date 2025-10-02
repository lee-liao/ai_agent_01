import asyncio
import json
from typing import Any, Dict, List, Optional, Tuple
import random

from app.database import execute_raw_command, execute_raw_query, check_table_exists


PROMPT_SEED = {
    "agent_planner": [
        {
            "version": 1,
            "template": "System: You are a pragmatic planner. Inputs: {goal} {constraints}",
            "metadata": {"tags": ["plan-exec", "baseline"], "locale": "en"},
            "changelog": "initial version",
            "created_by": "seed",
        },
        {
            "version": 2,
            "template": "System: Plan tasks concisely with numbered steps. Inputs: {goal} {constraints}",
            "metadata": {"tags": ["plan-exec", "short"], "locale": "en"},
            "changelog": "shortened instructions",
            "created_by": "seed",
        },
    ]
}

PROMPT_VARIABLES_SEED = {
    "agent_planner": [
        {
            "name": "goal",
            "type": "string",
            "required": True,
            "description": "goal"
        },
        {
            "name": "constraints",
            "type": "string",
            "required": False,
            "description": "constraints"
        }
    ]
}


async def ensure_schema() -> None:
    if not await check_table_exists("prompts"):
        await execute_raw_command(
            """
            CREATE TABLE IF NOT EXISTS prompts (
              id TEXT PRIMARY KEY,
              variables JSONB,
              created_at TIMESTAMP DEFAULT now()
            );
            """
        )
    else:
        # Check if variables column exists, if not add it
        try:
            await execute_raw_command(
                """
                ALTER TABLE prompts 
                ADD COLUMN IF NOT EXISTS variables JSONB
                """
            )
        except Exception as e:
            print(f"Note: Could not add variables column (may already exist): {e}")
    
    if not await check_table_exists("prompt_versions"):
        await execute_raw_command(
            """
            CREATE TABLE IF NOT EXISTS prompt_versions (
              id BIGSERIAL PRIMARY KEY,
              prompt_id TEXT REFERENCES prompts(id),
              version INT,
              template TEXT,
              metadata JSONB,
              changelog TEXT,
              created_by TEXT,
              created_at TIMESTAMP DEFAULT now(),
              UNIQUE(prompt_id, version)
            );
            """
        )
    if not await check_table_exists("prompt_deploys"):
        await execute_raw_command(
            """
            CREATE TABLE IF NOT EXISTS prompt_deploys (
              env TEXT,
              prompt_id TEXT,
              strategy TEXT,
              active_version INT,
              ab_alt_version INT,
              traffic_split INT,
              updated_at TIMESTAMP DEFAULT now(),
              PRIMARY KEY (env, prompt_id)
            );
            """
        )
    if not await check_table_exists("prompt_call_logs"):
        await execute_raw_command(
            """
            CREATE TABLE IF NOT EXISTS prompt_call_logs (
              id BIGSERIAL PRIMARY KEY,
              prompt_version_id BIGINT REFERENCES prompt_versions(id),
              success BOOLEAN,
              cost DECIMAL(10, 6),
              created_at TIMESTAMP DEFAULT now()
            );
            """
        )

    # seed minimal planner prompts if not present
    existing = await execute_raw_query(
        "SELECT COUNT(*) AS c FROM prompt_versions WHERE prompt_id = $1", "agent_planner"
    )
    count = (existing[0]["c"] if existing else 0) or 0
    if count == 0:
        await execute_raw_command(
            "INSERT INTO prompts(id, variables) VALUES($1, $2) ON CONFLICT DO NOTHING", 
            "agent_planner", 
            json.dumps(PROMPT_VARIABLES_SEED.get("agent_planner", []))
        )
        for row in PROMPT_SEED["agent_planner"]:
            await execute_raw_command(
                """
                INSERT INTO prompt_versions(prompt_id, version, template, metadata, changelog, created_by)
                VALUES($1,$2,$3,$4::jsonb,$5,$6)
                ON CONFLICT (prompt_id, version) DO NOTHING
                """,
                "agent_planner",
                row["version"],
                row["template"],
                json.dumps(row["metadata"]),
                row["changelog"],
                row["created_by"],
            )
        # default deploy fixed v1 for development
        await execute_raw_command(
            """
            INSERT INTO prompt_deploys(env, prompt_id, strategy, active_version, ab_alt_version, traffic_split)
            VALUES($1,$2,$3,$4,$5,$6)
            ON CONFLICT (env, prompt_id) DO NOTHING
            """,
            "development",
            "agent_planner",
            "fixed",
            1,
            None,
            0,
        )


async def list_versions(prompt_id: str) -> List[Dict[str, Any]]:
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"list_versions called with prompt_id: {prompt_id}")
    await ensure_schema()
    rows = await execute_raw_query(
        """
        SELECT version, template, metadata, changelog, created_by, created_at
        FROM prompt_versions WHERE prompt_id=$1 ORDER BY version DESC
        """,
        prompt_id,
    )
    return rows


async def create_version(prompt_id: str, template: str, metadata: Dict[str, Any], changelog: str, created_by: str) -> Dict[str, Any]:
    await ensure_schema()
    await execute_raw_command("INSERT INTO prompts(id) VALUES($1) ON CONFLICT DO NOTHING", prompt_id)
    current = await execute_raw_query(
        "SELECT COALESCE(MAX(version),0) AS v FROM prompt_versions WHERE prompt_id=$1",
        prompt_id,
    )
    next_version = int((current[0]["v"] if current else 0) or 0) + 1
    await execute_raw_command(
        """
        INSERT INTO prompt_versions(prompt_id, version, template, metadata, changelog, created_by)
        VALUES($1,$2,$3,$4::jsonb,$5,$6)
        """,
        prompt_id,
        next_version,
        template,
        json.dumps(metadata),
        changelog,
        created_by,
    )
    return {"prompt_id": prompt_id, "version": next_version}


async def get_version(prompt_id: str, version: int) -> Optional[Dict[str, Any]]:
    await ensure_schema()
    rows = await execute_raw_query(
        """
        SELECT version, template, metadata, changelog, created_by, created_at
        FROM prompt_versions WHERE prompt_id=$1 AND version=$2
        """,
        prompt_id,
        version,
    )
    return rows[0] if rows else None


async def set_deploy(env: str, prompt_id: str, strategy: str, active_version: int, ab_alt_version: Optional[int], traffic_split: Optional[int]) -> Dict[str, Any]:
    await ensure_schema()
    await execute_raw_command(
        """
        INSERT INTO prompt_deploys(env, prompt_id, strategy, active_version, ab_alt_version, traffic_split)
        VALUES($1,$2,$3,$4,$5,$6)
        ON CONFLICT (env, prompt_id)
        DO UPDATE SET strategy=EXCLUDED.strategy,
                      active_version=EXCLUDED.active_version,
                      ab_alt_version=EXCLUDED.ab_alt_version,
                      traffic_split=EXCLUDED.traffic_split,
                      updated_at=now()
        """,
        env,
        prompt_id,
        strategy,
        active_version,
        ab_alt_version,
        traffic_split or 0,
    )
    return {"env": env, "prompt_id": prompt_id, "strategy": strategy}


async def resolve_prompt(prompt_uri: str, env: str, user_key: Optional[str] = None) -> Dict[str, Any]:
    await ensure_schema()
    prompt_id = prompt_uri.replace("prompt://", "")
    deploy = await execute_raw_query(
        "SELECT strategy, active_version, ab_alt_version, traffic_split FROM prompt_deploys WHERE env=$1 AND prompt_id=$2",
        env,
        prompt_id,
    )
    if not deploy:
        # fallback to latest version
        versions = await list_versions(prompt_id)
        if not versions:
            return {"prompt_id": prompt_id, "version": 1, "template": "", "metadata": {}}
        version = int(versions[0]["version"])
    else:
        d = deploy[0]
        if d["strategy"] == "ab" and d.get("ab_alt_version") and int(d.get("traffic_split") or 0) > 0:
            # deterministic split
            key = user_key or "default"
            h = abs(hash(f"{prompt_id}:{env}:{key}")) % 100
            version = d["ab_alt_version"] if h < int(d["traffic_split"]) else d["active_version"]
        else:
            version = d["active_version"]

    row = await execute_raw_query(
        "SELECT id, version, template, metadata FROM prompt_versions WHERE prompt_id=$1 AND version=$2",
        prompt_id,
        version,
    )
    if not row:
        return {"prompt_id": prompt_id, "version": version, "template": "", "metadata": {}}
    r = row[0]
    return {"prompt_id": prompt_id, "version": r["version"], "template": r["template"], "metadata": r["metadata"], "prompt_version_id": r["id"]}


async def log_prompt_call(prompt_version_id: int, success: bool, cost: float) -> None:
    await ensure_schema()
    await execute_raw_command(
        """
        INSERT INTO prompt_call_logs(prompt_version_id, success, cost)
        VALUES($1, $2, $3)
        """,
        prompt_version_id,
        success,
        cost,
    )


async def get_version_stats(prompt_id: str) -> List[Dict[str, Any]]:
    await ensure_schema()
    rows = await execute_raw_query(
        """
        SELECT
            v.version,
            v.id AS prompt_version_id,
            COUNT(l.id) AS total_calls,
            SUM(CASE WHEN l.success THEN 1 ELSE 0 END) AS successful_calls,
            AVG(l.cost) AS avg_cost
        FROM prompt_versions v
        LEFT JOIN prompt_call_logs l ON v.id = l.prompt_version_id
        WHERE v.prompt_id = $1
        GROUP BY v.id, v.version
        ORDER BY v.version DESC
        """,
        prompt_id,
    )
    return [
        {
            "version": r["version"],
            "prompt_version_id": r["prompt_version_id"],
            "total_calls": r["total_calls"],
            "successful_calls": r["successful_calls"],
            "success_rate": r["successful_calls"] / r["total_calls"] if r["total_calls"] > 0 else 0,
            "avg_cost": r["avg_cost"] or 0,
        }
        for r in rows
    ]


async def list_prompts() -> List[Dict[str, Any]]:
    """Get all available prompts with their variables"""
    await ensure_schema()
    try:
        rows = await execute_raw_query(
            """
            SELECT id, variables, created_at
            FROM prompts
            ORDER BY created_at DESC
            """
        )
        # Parse the JSON strings back to Python objects
        for row in rows:
            if isinstance(row.get('variables'), str):
                try:
                    row['variables'] = json.loads(row['variables'])
                except (json.JSONDecodeError, TypeError):
                    row['variables'] = None
        return rows
    except Exception as e:
        print(f"Error in list_prompts: {e}")
        import traceback
        traceback.print_exc()
        return []


async def get_prompt(prompt_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific prompt by ID"""
    await ensure_schema()
    try:
        rows = await execute_raw_query(
            """
            SELECT id, variables, created_at
            FROM prompts
            WHERE id = $1
            """,
            prompt_id
        )
        if rows:
            # Parse the JSON string back to a Python object
            row = rows[0]
            if isinstance(row.get('variables'), str):
                try:
                    row['variables'] = json.loads(row['variables'])
                except (json.JSONDecodeError, TypeError):
                    row['variables'] = None
            return row
        return None
    except Exception as e:
        print(f"Error in get_prompt: {e}")
        import traceback
        traceback.print_exc()
        return None


async def update_prompt_variables(prompt_id: str, variables: Dict[str, Any]) -> None:
    """Update the variables for a specific prompt"""
    await ensure_schema()
    await execute_raw_command(
        """
        INSERT INTO prompts(id, variables)
        VALUES($1, $2::jsonb)
        ON CONFLICT (id)
        DO UPDATE SET variables = EXCLUDED.variables
        """,
        prompt_id,
        json.dumps(variables)
    )


async def delete_version(prompt_id: str, version: int) -> Dict[str, Any]:
    """Delete a specific version of a prompt"""
    await ensure_schema()
    
    # First check if the version exists
    existing = await execute_raw_query(
        "SELECT id FROM prompt_versions WHERE prompt_id = $1 AND version = $2",
        prompt_id, version
    )
    
    if not existing:
        raise ValueError(f"Version {version} of prompt '{prompt_id}' not found")
    
    # Get the version id for foreign key references
    version_id = existing[0]["id"]
    
    # Delete associated logs first (due to foreign key constraint)
    await execute_raw_command(
        "DELETE FROM prompt_call_logs WHERE prompt_version_id = $1",
        version_id
    )
    
    # Delete the version itself
    await execute_raw_command(
        "DELETE FROM prompt_versions WHERE prompt_id = $1 AND version = $2",
        prompt_id, version
    )
    
    return {"status": "success", "message": f"Version {version} of prompt '{prompt_id}' deleted successfully"}


async def update_version(prompt_id: str, version: int, template: str, changelog: str) -> Dict[str, Any]:
    """Update an existing version of a prompt"""
    await ensure_schema()
    
    # First check if the version exists
    existing = await execute_raw_query(
        "SELECT id FROM prompt_versions WHERE prompt_id = $1 AND version = $2",
        prompt_id, version
    )
    
    if not existing:
        raise ValueError(f"Version {version} of prompt '{prompt_id}' not found")
    
    # Update the version
    await execute_raw_command(
        """
        UPDATE prompt_versions 
        SET template = $3, changelog = $4
        WHERE prompt_id = $1 AND version = $2
        """,
        prompt_id, version, template, changelog
    )
    
    return {"status": "success", "message": f"Version {version} of prompt '{prompt_id}' updated successfully"}
