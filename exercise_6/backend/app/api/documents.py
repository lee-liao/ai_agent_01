"""
Exercise 6: Documents API Routes
Handles individual document operations and metadata
"""

import os
import uuid
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.database import execute_raw_command, execute_raw_query
from app.services.rag.document_processor import document_processor

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])
logger = logging.getLogger(__name__)

# Define the upload directory relative to the project root
UPLOAD_DIRECTORY = Path(os.getenv("UPLOAD_DIRECTORY", "D:\\MyCode\\AI\\Victoria\\lesson3\\ai_agent_01\\exercise_6\\uploads"))
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)


async def process_document_background(document_id: str, file_path: str, filename: str):
    """
    Background task to process a document.
    """
    logger.info(f"Starting background processing for document {document_id}")
    try:
        processing_result = await document_processor.process_document(
            file_path=str(file_path),
            filename=filename,
            document_id=document_id
        )

        if processing_result["processing_status"] == "completed":
            await execute_raw_command(
                "UPDATE documents SET status = 'completed', processed_at = NOW() WHERE id = $1",
                document_id
            )
            logger.info(f"Successfully processed document {document_id}")
        else:
            error_message = processing_result.get("error", "Unknown processing error")
            await execute_raw_command(
                "UPDATE documents SET status = 'failed', processing_error = $1 WHERE id = $2",
                error_message,
                document_id
            )
            logger.error(f"Failed to process document {document_id}: {error_message}")

    except Exception as e:
        logger.error(f"Unhandled error in background processing for document {document_id}: {e}")
        await execute_raw_command(
            "UPDATE documents SET status = 'failed', processing_error = $1 WHERE id = $2",
            str(e),
            document_id
        )


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    """Upload a document to the knowledge base"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    document_id = uuid.uuid4()
    original_filename = file.filename
    file_extension = Path(original_filename).suffix
    saved_filename = f"{document_id}{file_extension}"
    file_path = UPLOAD_DIRECTORY / saved_filename

    try:
        # Save the file
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        logger.info(f"Saved uploaded file to {file_path}")

        # Get file size
        file_size = file_path.stat().st_size

        # Create a record in the database
        insert_query = """
            INSERT INTO documents (id, knowledge_base_id, filename, original_filename, file_path, file_size, file_type, mime_type, status)
            VALUES ($1, (SELECT id FROM knowledge_bases WHERE name = 'Default Knowledge Base'), $2, $3, $4, $5, $6, $7, 'processing')
            RETURNING id, filename, status, created_at;
        """
        new_doc = await execute_raw_query(
            insert_query,
            document_id,
            saved_filename,
            original_filename,
            str(file_path),
            file_size,
            file_extension,
            file.content_type
        )

        if not new_doc:
            raise HTTPException(status_code=500, detail="Failed to create document record in database")

        # Add background task for processing
        background_tasks.add_task(
            process_document_background,
            document_id=document_id,
            file_path=str(file_path),
            filename=original_filename
        )

        return {
            "status": "success",
            "message": "Document upload initiated. Processing in background.",
            "data": new_doc[0]
        }

    except Exception as e:
        logger.error(f"Error during document upload: {e}")
        # Clean up saved file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@router.get("/")
async def list_documents(
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """List all documents with optional filtering"""
    base_query = "SELECT id, filename, original_filename, status, created_at, updated_at, file_size, file_type FROM documents"
    params = []
    where_clauses = []

    if status:
        params.append(status)
        where_clauses.append(f"status = ${len(params)}")

    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)

    # Get total count
    count_query = f"SELECT COUNT(*) FROM ({base_query}) as sub"
    total = await execute_raw_query(count_query, *params)
    total_count = total[0]['count'] if total else 0

    # Get paginated results
    params.append(limit)
    params.append(offset)
    paginated_query = f"{base_query} ORDER BY created_at DESC LIMIT ${len(params)-1} OFFSET ${len(params)}"
    
    documents = await execute_raw_query(paginated_query, *params)

    return {
        "status": "success",
        "data": documents,
        "total": total_count,
        "limit": limit,
        "offset": offset
    }


@router.get("/{document_id}")
async def get_document(document_id: str) -> Dict[str, Any]:
    """Get a specific document by ID"""
    query = "SELECT * FROM documents WHERE id = $1"
    document = await execute_raw_query(query, document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "status": "success",
        "data": document[0]
    }


@router.put("/{document_id}")
async def update_document(document_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update document metadata"""
    # This is a simplified update. In a real app, you'd have more robust field validation.
    allowed_fields = ["title", "author", "tags", "description"]
    
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

    params.append(document_id)
    query = f"UPDATE documents SET {', '.join(set_clauses)}, updated_at = NOW() WHERE id = ${param_idx} RETURNING *"
    
    updated_document = await execute_raw_query(query, *params)

    if not updated_document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "status": "success",
        "message": "Document updated successfully",
        "data": updated_document[0]
    }


@router.get("/{document_id}/chunks")
async def get_document_chunks(document_id: str) -> Dict[str, Any]:
    """Get all chunks for a specific document"""
    query = "SELECT id, chunk_index, content, token_count, char_count FROM document_chunks WHERE document_id = $1 ORDER BY chunk_index"
    chunks = await execute_raw_query(query, document_id)
    
    return {
        "status": "success",
        "data": chunks,
        "total": len(chunks)
    }
