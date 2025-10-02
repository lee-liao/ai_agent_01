import asyncio
import logging
from datetime import datetime, timedelta
from app.database import execute_raw_query
from app.services.prompt_store import set_deploy, ensure_schema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_and_perform_rollback():
    """Checks for underperforming A/B tests and rolls them back."""
    try:
        await ensure_schema()
        active_ab_tests = await execute_raw_query(
            """SELECT prompt_id, active_version, ab_alt_version
               FROM prompt_deploys
               WHERE strategy = 'ab' AND ab_alt_version IS NOT NULL"""
        )

        for test in active_ab_tests:
            prompt_id = test['prompt_id']
            v_a_id = test['active_version']
            v_b_id = test['ab_alt_version']

            ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)

            # Get failure rates
            failure_rate_a = await get_failure_rate(v_a_id, ten_minutes_ago)
            failure_rate_b = await get_failure_rate(v_b_id, ten_minutes_ago)

            # Check if rollback is needed
            if failure_rate_b > failure_rate_a + 0.05:
                logger.info(f"Rolling back A/B test for prompt '{prompt_id}'. "
                            f"Version {v_b_id} failure rate ({failure_rate_b:.2%}) is > 5pp above "
                            f"version {v_a_id} ({failure_rate_a:.2%}).")
                await set_deploy(
                    env='development',  # Assuming development env for now
                    prompt_id=prompt_id,
                    strategy='fixed',
                    active_version=v_a_id,
                    ab_alt_version=None,
                    traffic_split=0
                )
    except Exception as e:
        logger.error(f"Error in auto-rollback check: {e}", exc_info=True)

async def get_failure_rate(version_id: int, since: datetime) -> float:
    """Calculates the failure rate for a given prompt version since a specific time."""
    await ensure_schema()
    result = await execute_raw_query(
        """SELECT CAST(SUM(CASE WHEN success = false THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*)
           FROM prompt_call_logs
           WHERE prompt_version_id = $1 AND created_at >= $2""",
        version_id, since
    )
    return result[0][0] if result and result[0] else 0.0

async def background_rollback_task():
    """Runs the rollback check periodically."""
    while True:
        await asyncio.sleep(60)  # Check every minute
        await check_and_perform_rollback()

def start_rollback_service():
    """Initiates the background rollback task."""
    logger.info("Starting background auto-rollback service...")
    asyncio.create_task(background_rollback_task())
