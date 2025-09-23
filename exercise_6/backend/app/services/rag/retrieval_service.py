"""
Retrieval Service for RAG System
Handles semantic search and document retrieval from vector database
"""

import logging
from typing import List, Dict, Any, Optional
import asyncio

import openai
import chromadb
from chromadb.config import Settings

from app.config import settings

logger = logging.getLogger(__name__)

class RetrievalService:
    """Handles semantic search and document retrieval"""
    
    def __init__(self):
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.HttpClient(
            host=settings.chromadb_host,
            port=settings.chromadb_port,
            settings=Settings(allow_reset=True)
        )
        
        # Get collection
        self.collection_name = "rag_documents"
        try:
            self.collection = self.chroma_client.get_collection(self.collection_name)
            logger.info(f"Connected to ChromaDB collection: {self.collection_name}")
        except Exception as e:
            logger.warning(f"ChromaDB collection not found: {e}")
            self.collection = None
    
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
        if not self.collection:
            logger.warning("ChromaDB collection not available")
            return []
        
        try:
            # Use configured defaults if not provided
            max_results = max_results or settings.max_chunks_per_query
            similarity_threshold = similarity_threshold or settings.similarity_threshold
            
            logger.info(f"Searching for: '{query}' (max_results={max_results}, threshold={similarity_threshold})")
            
            # Generate embedding for the query
            query_embedding = await self._generate_query_embedding(query)
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Process and filter results
            relevant_chunks = []
            
            if results['ids'] and results['ids'][0]:  # Check if we have results
                for i, (chunk_id, document, metadata, distance) in enumerate(zip(
                    results['ids'][0],
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    # Convert distance to similarity score (ChromaDB uses cosine distance)
                    similarity_score = 1 - distance
                    
                    # Filter by similarity threshold
                    if similarity_score >= similarity_threshold:
                        chunk_info = {
                            "chunk_id": chunk_id,
                            "document_id": metadata.get("document_id"),
                            "filename": metadata.get("filename"),
                            "chunk_index": metadata.get("chunk_index"),
                            "content": document,
                            "similarity_score": round(similarity_score, 4),
                            "chunk_length": len(document),
                            "metadata": metadata
                        }
                        relevant_chunks.append(chunk_info)
            
            logger.info(f"Found {len(relevant_chunks)} relevant chunks (filtered from {len(results['ids'][0]) if results['ids'] else 0} total)")
            
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
        if not self.collection:
            return []
        
        try:
            results = self.collection.get(
                where={"document_id": document_id},
                include=['documents', 'metadatas']
            )
            
            chunks = []
            if results['ids']:
                for chunk_id, document, metadata in zip(
                    results['ids'],
                    results['documents'],
                    results['metadatas']
                ):
                    chunk_info = {
                        "chunk_id": chunk_id,
                        "document_id": document_id,
                        "filename": metadata.get("filename"),
                        "chunk_index": metadata.get("chunk_index"),
                        "content": document,
                        "chunk_length": len(document),
                        "metadata": metadata
                    }
                    chunks.append(chunk_info)
            
            # Sort by chunk index
            chunks.sort(key=lambda x: x.get('chunk_index', 0))
            return chunks
            
        except Exception as e:
            logger.error(f"Error getting document chunks: {e}")
            return []
    
    async def search_similar_chunks(self, chunk_id: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Find chunks similar to a given chunk"""
        if not self.collection:
            return []
        
        try:
            # Get the chunk content
            chunk_result = self.collection.get(
                ids=[chunk_id],
                include=['documents']
            )
            
            if not chunk_result['documents']:
                return []
            
            chunk_content = chunk_result['documents'][0]
            
            # Search for similar chunks
            return await self.search_documents(
                query=chunk_content,
                max_results=max_results + 1  # +1 to exclude the original chunk
            )
            
        except Exception as e:
            logger.error(f"Error finding similar chunks: {e}")
            return []
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the document collection"""
        if not self.collection:
            return {
                "status": "unavailable",
                "total_chunks": 0,
                "collection_name": self.collection_name
            }
        
        try:
            count = self.collection.count()
            
            # Get sample of documents to show variety
            sample_results = self.collection.get(
                limit=10,
                include=['metadatas']
            )
            
            unique_documents = set()
            if sample_results['metadatas']:
                for metadata in sample_results['metadatas']:
                    if metadata.get('document_id'):
                        unique_documents.add(metadata['document_id'])
            
            return {
                "status": "available",
                "total_chunks": count,
                "collection_name": self.collection_name,
                "sample_documents": len(unique_documents),
                "embedding_model": settings.rag_embedding_model
            }
            
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {
                "status": "error",
                "error": str(e),
                "collection_name": self.collection_name
            }

# Global instance
retrieval_service = RetrievalService()
