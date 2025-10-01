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

        # Convert embeddings to pgvector format (string representation)
        question_embedding_str = '[' + ','.join(map(str, question_embedding)) + ']'
        answer_embedding_str = '[' + ','.join(map(str, answer_embedding)) + ']'

        await execute_raw_command(
            """
            UPDATE qa_pairs 
            SET question_embedding = $1, answer_embedding = $2, updated_at = NOW()
            WHERE id = $3
            """,
            question_embedding_str,
            answer_embedding_str,
            qa_id
        )
        
        logger.info(f"Successfully added embeddings for Q&A pair {qa_id}")
    except Exception as e:
        logger.error(f"Failed to generate embeddings for Q&A pair {qa_id}: {e}")
        # Don't raise exception as this is a background task


@router.get("/")
async def list_qa_pairs(
    limit: Optional[int] = 100,
    offset: Optional[int] = 0
) -> Dict[str, Any]:
    """List all Q&A pairs"""
    try:
        # Query database for Q&A pairs
        results = await execute_raw_query(
            """
            SELECT id, question, answer, tags, created_at, updated_at
            FROM qa_pairs
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """,
            limit,
            offset
        )
        
        # Convert results to list of dictionaries
        qa_pairs = []
        for row in results:
            qa_pairs.append({
                "id": row["id"],
                "question": row["question"],
                "answer": row["answer"],
                "tags": row["tags"] if row["tags"] else [],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
            })
        
        return {
            "status": "success",
            "data": qa_pairs
        }
    except Exception as e:
        logger.error(f"Failed to list Q&A pairs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Q&A pairs")


@router.post("/")
async def create_qa_pair(
    qa_data: Dict[str, Any],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Create a new Q&A pair"""
    try:
        # Validate input
        question = qa_data.get("question")
        answer = qa_data.get("answer")
        tags = qa_data.get("tags", [])
        
        if not question or not answer:
            raise HTTPException(status_code=400, detail="Question and answer are required")
        
        # Generate UUID for the new Q&A pair
        qa_id = str(uuid.uuid4())
        
        # Insert into database
        await execute_raw_command(
            """
            INSERT INTO qa_pairs (id, question, answer, tags, created_at, updated_at)
            VALUES ($1, $2, $3, $4, NOW(), NOW())
            """,
            qa_id,
            question,
            answer,
            tags
        )
        
        # Add embedding generation as background task
        background_tasks.add_task(add_embeddings_background, qa_id, question, answer)
        
        return {
            "status": "success",
            "message": "Q&A pair created successfully",
            "data": {
                "id": qa_id
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create Q&A pair: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Q&A pair")


@router.put("/{qa_id}")
async def update_qa_pair(
    qa_id: str,
    qa_data: Dict[str, Any],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Update an existing Q&A pair"""
    try:
        # Check if Q&A pair exists
        existing = await execute_raw_query(
            "SELECT id FROM qa_pairs WHERE id = $1",
            qa_id
        )
        
        if not existing:
            raise HTTPException(status_code=404, detail="Q&A pair not found")
        
        # Update Q&A pair
        question = qa_data.get("question")
        answer = qa_data.get("answer")
        tags = qa_data.get("tags", [])
        
        await execute_raw_command(
            """
            UPDATE qa_pairs
            SET question = COALESCE($1, question),
                answer = COALESCE($2, answer),
                tags = $3,
                updated_at = NOW()
            WHERE id = $4
            """,
            question,
            answer,
            tags,
            qa_id
        )
        
        # If question or answer was updated, regenerate embeddings
        if question or answer:
            # Get the current values from database
            results = await execute_raw_query(
                "SELECT question, answer FROM qa_pairs WHERE id = $1",
                qa_id
            )
            if results:
                current_question, current_answer = results[0]["question"], results[0]["answer"]
                background_tasks.add_task(
                    add_embeddings_background, 
                    qa_id, 
                    current_question, 
                    current_answer
                )
        
        return {
            "status": "success",
            "message": "Q&A pair updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update Q&A pair {qa_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Q&A pair")


@router.delete("/{qa_id}")
async def delete_qa_pair(qa_id: str) -> Dict[str, Any]:
    """Delete a Q&A pair"""
    try:
        # Check if Q&A pair exists
        existing = await execute_raw_query(
            "SELECT id FROM qa_pairs WHERE id = $1",
            qa_id
        )
        
        if not existing:
            raise HTTPException(status_code=404, detail="Q&A pair not found")
        
        # Delete from database
        await execute_raw_command(
            "DELETE FROM qa_pairs WHERE id = $1",
            qa_id
        )
        
        return {
            "status": "success",
            "message": "Q&A pair deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete Q&A pair {qa_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete Q&A pair")