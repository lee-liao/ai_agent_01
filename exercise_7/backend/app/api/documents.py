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
UPLOAD_DIRECTORY = Path(os.getenv("UPLOAD_DIRECTORY", "./uploads"))
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)


async def process_document_background(document_id: str, file_path: str, filename: str):
    """
    Background task to process a document.
    """
    logger.info(f"Starting background processing for document {document_id}")
    try:
        processing_result = await document_processor.process_document(
            file_path=file_path,
            filename=filename,
            document_id=document_id
        )
        
        # Update document status in database
        import json
        await execute_raw_command(
            """
            UPDATE documents 
            SET status = $1, processed_at = NOW(), metadata = $2::jsonb
            WHERE id = $3
            """,
            processing_result["status"],
            json.dumps(processing_result.get("metadata", {})),
            document_id
        )
        
        logger.info(f"Completed background processing for document {document_id}")
    except Exception as e:
        logger.error(f"Failed to process document {document_id}: {e}")
        # Update document status to failed
        await execute_raw_command(
            """
            UPDATE documents 
            SET status = $1, processing_error = $2
            WHERE id = $3
            """,
            "failed",
            str(e),
            document_id
        )


@router.get("/")
async def list_documents(
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """List all documents with optional filtering"""
    try:
        # Build query with optional status filter
        query = "SELECT id, filename, original_filename, file_size, file_type, status, title, created_at, updated_at, processed_at, metadata FROM documents"
        params = []
        
        if status:
            query += " WHERE status = $1"
            params.append(status)
        
        # Add LIMIT and OFFSET with correct parameter indices
        if status:
            # If we have a status parameter, LIMIT is $2 and OFFSET is $3
            query += " ORDER BY created_at DESC LIMIT $2 OFFSET $3"
            params.extend([limit, offset])
        else:
            # If no status parameter, LIMIT is $1 and OFFSET is $2
            query += " ORDER BY created_at DESC LIMIT $1 OFFSET $2"
            params.extend([limit, offset])
        
        # Execute query
        results = await execute_raw_query(query, *params)
        
        # Convert results to list of dictionaries
        documents = []
        for row in results:
            documents.append({
                "id": row["id"],
                "filename": row["filename"],
                "original_filename": row["original_filename"] if row["original_filename"] else row["filename"],
                "file_size": row["file_size"] if row["file_size"] else 0,
                "file_type": row["file_type"] if row["file_type"] else "",
                "status": row["status"],
                "title": row["title"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                "processed_at": row["processed_at"].isoformat() if row["processed_at"] else None,
                "metadata": row["metadata"] if row["metadata"] else {}
            })
        
        return {
            "status": "success",
            "data": documents
        }
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> Dict[str, Any]:
    """Upload a document for processing"""
    try:
        # Validate file type
        allowed_types = ['pdf', 'txt', 'docx', 'md']
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        
        if file_extension not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed. Allowed types: {allowed_types}"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        unique_filename = f"{file_id}.{file_extension}"
        file_path = UPLOAD_DIRECTORY / unique_filename
        
        # Save file to disk
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Get file stats
        file_stat = file_path.stat()
        file_size = file_stat.st_size
        
        # Get default knowledge base ID
        kb_results = await execute_raw_query(
            "SELECT id FROM knowledge_bases WHERE name = 'Default Knowledge Base'"
        )
        if not kb_results:
            raise HTTPException(status_code=500, detail="Default knowledge base not found")
        
        knowledge_base_id = kb_results[0]["id"]

        # Save document metadata to database
        await execute_raw_command(
            """
            INSERT INTO documents (id, knowledge_base_id, filename, original_filename, file_path, file_size, file_type, mime_type, status, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
            """,
            file_id,
            knowledge_base_id,
            unique_filename,  # Saved filename
            file.filename,    # Original filename
            str(file_path),   # Full path
            file_size,        # File size
            file_extension,   # File type
            file.content_type or "",  # MIME type
            "processing"        # Status
        )
        
        # Add document processing as background task
        background_tasks.add_task(process_document_background, file_id, str(file_path), file.filename)
        
        return {
            "status": "success",
            "message": "Document uploaded successfully",
            "data": {
                "id": file_id,
                "filename": file.filename,
                "original_filename": file.filename,
                "file_size": file_size,
                "file_type": file_extension,
                "status": "processing"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload document")


@router.delete("/{document_id}")
async def delete_document(document_id: str) -> Dict[str, Any]:
    """Delete a document"""
    try:
        # Get document info
        results = await execute_raw_query(
            "SELECT file_path FROM documents WHERE id = $1",
            document_id
        )
        
        if not results:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = results[0]["file_path"]
        
        # Delete file from disk if it exists
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database
        await execute_raw_command(
            "DELETE FROM documents WHERE id = $1",
            document_id
        )
        
        return {
            "status": "success",
            "message": "Document deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")