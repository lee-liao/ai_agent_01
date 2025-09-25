"""
Exercise 6: Q&A Pairs API Routes
Handles question-answer pair management
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
import uuid
import logging

from app.database import execute_raw_query, execute_raw_command
from app.services.vector_service import vector_service

router = APIRouter(prefix="/api/v1/qa-pairs", tags=["Q&A Pairs"])
logger = logging.getLogger(__name__)


async def add_embeddings_background(qa_id: str, question: str, answer: str):
    """
    Background task to generate and add embeddings to a Q&A pair.
    """
    try:
        logger.info(f"Generating embeddings for Q&A pair {qa_id}")
        question_embedding = await vector_service.generate_embedding(question)
        answer_embedding = await vector_service.generate_embedding(answer)

        await execute_raw_command(
            """
            UPDATE qa_pairs
            SET question_embedding = $1, answer_embedding = $2
            WHERE id = $3
            """,
            question_embedding,
            answer_embedding,
            qa_id,
        )
        logger.info(f"Successfully added embeddings to Q&A pair {qa_id}")
    except Exception as e:
        logger.error(f"Failed to generate embeddings for Q&A pair {qa_id}: {e}")
        # Optionally, you could set a status on the qa_pair to indicate failure.


@router.get("/")
async def list_qa_pairs(
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    tag: Optional[str] = None
) -> Dict[str, Any]:
    """List all Q&A pairs with optional filtering"""
    params = []
    where_clauses = ["status = 'active'"]

    if tag:
        params.append(tag)
        where_clauses.append(f"${len(params)} = ANY(tags)")

    query = f"""
        SELECT id, question, answer, tags, created_at, updated_at
        FROM qa_pairs
        WHERE {" AND ".join(where_clauses)}
        ORDER BY created_at DESC
        LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
    """
    params.extend([limit, offset])
    
    pairs = await execute_raw_query(query, *params)

    count_query = f"""
        SELECT COUNT(*) FROM qa_pairs WHERE {" AND ".join(where_clauses)}
    """
    # The params for count query should not include limit and offset
    count_params = params[:-2]
    total = await execute_raw_query(count_query, *count_params)
    total_count = total[0]['count'] if total else 0

    return {
        "status": "success",
        "data": pairs,
        "total": total_count,
        "limit": limit,
        "offset": offset,
    }


@router.post("/")
async def create_qa_pair(
    qa_data: Dict[str, Any], background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Create a new Q&A pair"""
    question = qa_data.get("question")
    answer = qa_data.get("answer")
    tags = qa_data.get("tags", [])

    if not question or not answer:
        raise HTTPException(status_code=400, detail="Question and answer are required")

    qa_id = uuid.uuid4()

    query = """
        INSERT INTO qa_pairs (id, knowledge_base_id, question, answer, tags, status)
        VALUES ($1, (SELECT id FROM knowledge_bases WHERE name = 'Default Knowledge Base'), $2, $3, $4, 'active')
        RETURNING id, question, answer, tags, created_at, updated_at;
    """
    
    new_pair = await execute_raw_query(
        query, qa_id, question, answer, tags
    )

    if not new_pair:
        raise HTTPException(status_code=500, detail="Failed to create Q&A pair")

    # Generate and add embeddings in the background
    background_tasks.add_task(add_embeddings_background, qa_id, question, answer)

    return {
        "status": "success",
        "message": "Q&A pair created successfully. Embeddings are being generated in the background.",
        "data": new_pair[0],
    }


@router.get("/{qa_id}")
async def get_qa_pair(qa_id: str) -> Dict[str, Any]:
    """Get a specific Q&A pair by ID"""
    query = "SELECT id, question, answer, tags, created_at, updated_at FROM qa_pairs WHERE id = $1 AND status = 'active'"
    qa_pair = await execute_raw_query(query, qa_id)
    
    if not qa_pair:
        raise HTTPException(status_code=404, detail="Q&A pair not found")
    
    return {"status": "success", "data": qa_pair[0]}


@router.put("/{qa_id}")
async def update_qa_pair(
    qa_id: str, update_data: Dict[str, Any], background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Update a Q&A pair"""
    # This is a simplified update. In a real app, you'd have more robust field validation.
    allowed_fields = ["question", "answer", "tags"]
    
    set_clauses = []
    params = []
    param_idx = 1

    for field, value in update_data.items():
        if field in allowed_fields:
            set_clauses.append(f"{field} = ${param_idx}")
            params.append(value)
            param_idx += 1

    if not set_clauses:
        raise HTTPException(status_code=400, detail="No updatable fields provided.")

    params.append(qa_id)
    query = f"UPDATE qa_pairs SET {', '.join(set_clauses)}, updated_at = NOW() WHERE id = ${param_idx} AND status = 'active' RETURNING *"
    
    updated_pair = await execute_raw_query(query, *params)

    if not updated_pair:
        raise HTTPException(status_code=404, detail="Q&A pair not found")

    # Re-generate embeddings in the background if question or answer changed
    if "question" in update_data or "answer" in update_data:
        updated_question = update_data.get("question", updated_pair[0]["question"])
        updated_answer = update_data.get("answer", updated_pair[0]["answer"])
        background_tasks.add_task(add_embeddings_background, qa_id, updated_question, updated_answer)

    return {
        "status": "success",
        "message": "Q&A pair updated successfully. Embeddings are being updated in the background if necessary.",
        "data": updated_pair[0],
    }


@router.delete("/{qa_id}")
async def delete_qa_pair(qa_id: str) -> Dict[str, Any]:
    """Delete a Q&A pair (soft delete by changing status)"""
    query = "UPDATE qa_pairs SET status = 'archived', updated_at = NOW() WHERE id = $1 AND status = 'active' RETURNING id"
    deleted_pair = await execute_raw_query(query, qa_id)

    if not deleted_pair:
        raise HTTPException(status_code=404, detail="Q&A pair not found")

    return {"status": "success", "message": f"Q&A pair {qa_id} deleted successfully"}

# The /usage endpoint is removed as it was part of the mock implementation
# and the database schema does not have usage_count or last_used columns for qa_pairs.