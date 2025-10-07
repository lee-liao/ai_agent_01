"""
Retrieval Service for RAG System
Handles semantic search and document retrieval from vector database
"""

import logging
from typing import List, Dict, Any, Optional
import asyncio

import openai
# ChromaDB imports removed - now using PostgreSQL + pgvector for documents

from app.config import settings
from app.database import get_connection

logger = logging.getLogger(__name__)

class RetrievalService:
    """Handles semantic search and document retrieval"""
    
    def __init__(self):
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        
        # Initialize PostgreSQL Vector Service for document retrieval
        from app.services.vector_service import PostgreSQLVectorService
        self.vector_service = PostgreSQLVectorService()
        logger.info("Retrieval service configured to use PostgreSQL + pgvector")
    
    async def search_documents(
        self, 
        query: str, 
        max_results: int = None,
        similarity_threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks based on query
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of relevant document chunks with metadata
        """
        try:
            # Use configured defaults if not provided
            max_results = max_results or settings.max_chunks_per_query
            similarity_threshold = similarity_threshold or settings.similarity_threshold
            
            logger.info(f"Searching for: '{query}' (max_results={max_results}, threshold={similarity_threshold})")
            
            # Initialize vector service and search in PostgreSQL
            await self.vector_service.initialize()
            relevant_chunks = await self.vector_service.search_document_chunks(
                query=query,
                max_results=max_results,
                similarity_threshold=similarity_threshold
            )
            
            logger.info(f"Found {len(relevant_chunks)} relevant chunks from PostgreSQL + pgvector")
            
            # Sort by similarity score (highest first)
            relevant_chunks.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    async def _generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for search query"""
        try:
            def generate_sync():
                response = self.openai_client.embeddings.create(
                    model=settings.rag_embedding_model,
                    input=[query]
                )
                return response.data[0].embedding
            
            embedding = await asyncio.get_event_loop().run_in_executor(None, generate_sync)
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise
    
    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific document"""
        try:
            conn = await get_connection()
            try:
                chunks = await conn.fetch("""
                    SELECT id, chunk_index, content, token_count, char_count, metadata
                    FROM document_chunks 
                    WHERE document_id = $1 
                    ORDER BY chunk_index
                """, document_id)
                
                result_chunks = []
                for row in chunks:
                    chunk_info = {
                        "chunk_id": str(row["id"]),
                        "document_id": document_id,
                        "filename": row["metadata"].get("filename") if row["metadata"] else None,
                        "chunk_index": row["chunk_index"],
                        "content": row["content"],
                        "chunk_length": row["char_count"],
                        "token_count": row["token_count"],
                        "metadata": row["metadata"] or {}
                    }
                    result_chunks.append(chunk_info)
                
                return result_chunks
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Error getting document chunks: {e}")
            return []
    
    async def search_similar_chunks(self, chunk_id: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Find chunks similar to a given chunk"""
        try:
            conn = await get_connection()
            try:
                # Get the chunk content
                chunk_row = await conn.fetchrow("""
                    SELECT content FROM document_chunks WHERE id = $1
                """, chunk_id)
                
                if not chunk_row:
                    return []
                
                chunk_content = chunk_row["content"]
                
                # Search for similar chunks using the content
                return await self.search_documents(
                    query=chunk_content,
                    max_results=max_results + 1  # +1 to exclude the original chunk
                )
            finally:
                await conn.close()
            
        except Exception as e:
            logger.error(f"Error finding similar chunks: {e}")
            return []
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the document collection from PostgreSQL"""
        try:
            await self.vector_service.initialize()
            conn = await get_connection()
            try:
                # Get document chunks count
                count = await conn.fetchval("SELECT COUNT(*) FROM document_chunks")
                
                # Get unique documents count
                doc_count = await conn.fetchval("SELECT COUNT(DISTINCT document_id) FROM document_chunks")
                
                return {
                    "status": "available",
                    "total_chunks": count,
                    "database": "postgresql_pgvector",
                    "sample_documents": doc_count,
                    "embedding_model": settings.rag_embedding_model
                }
            finally:
                await conn.close()
        except Exception as e:
            return {
                "status": "error",
                "total_chunks": 0,
                "database": "postgresql_pgvector",
                "error": str(e)
            }

# Global instance
retrieval_service = RetrievalService()
