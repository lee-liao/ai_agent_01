"""
Document Processing Service for RAG System
Handles document parsing, chunking, and embedding generation
"""

import logging
import os
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio

# Document processing
import PyPDF2
from docx import Document
import openai

# Vector storage
import chromadb
from chromadb.config import Settings

from app.config import settings

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Handles document processing, chunking, and embedding generation"""
    
    def __init__(self):
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        
        # Simple text splitter
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.HttpClient(
            host=settings.chromadb_host,
            port=settings.chromadb_port,
            settings=Settings(allow_reset=True)
        )
        
        # Get or create collection
        self.collection_name = "rag_documents"
        try:
            self.collection = self.chroma_client.get_collection(self.collection_name)
            logger.info(f"Connected to existing ChromaDB collection: {self.collection_name}")
        except Exception:
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "RAG document embeddings"}
            )
            logger.info(f"Created new ChromaDB collection: {self.collection_name}")
    
    async def process_document(self, file_path: str, filename: str, document_id: str) -> Dict[str, Any]:
        """
        Process a document: extract text, chunk it, generate embeddings, and store in vector DB
        
        Args:
            file_path: Path to the uploaded file
            filename: Original filename
            document_id: Unique document identifier
            
        Returns:
            Dictionary with processing results
        """
        try:
            logger.info(f"Processing document: {filename} (ID: {document_id})")
            
            # Extract text from document
            text_content = await self._extract_text(file_path, filename)
            
            if not text_content.strip():
                raise ValueError("No text content extracted from document")
            
            # Split text into chunks
            chunks = self._split_text(text_content)
            logger.info(f"Split document into {len(chunks)} chunks")
            
            # Generate embeddings for chunks
            chunk_embeddings = await self._generate_embeddings(chunks)
            
            # Store chunks and embeddings in ChromaDB
            chunk_ids = []
            chunk_metadatas = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, chunk_embeddings)):
                chunk_id = f"{document_id}_chunk_{i}"
                chunk_ids.append(chunk_id)
                
                metadata = {
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_index": i,
                    "chunk_text": chunk[:500],  # Store first 500 chars for preview
                    "chunk_length": len(chunk)
                }
                chunk_metadatas.append(metadata)
            
            # Add to ChromaDB
            self.collection.add(
                ids=chunk_ids,
                embeddings=chunk_embeddings,
                documents=chunks,
                metadatas=chunk_metadatas
            )
            
            logger.info(f"Successfully stored {len(chunks)} chunks in ChromaDB")
            
            return {
                "document_id": document_id,
                "filename": filename,
                "chunks_count": len(chunks),
                "total_characters": len(text_content),
                "processing_status": "completed",
                "chunk_ids": chunk_ids
            }
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}")
            return {
                "document_id": document_id,
                "filename": filename,
                "processing_status": "failed",
                "error": str(e)
            }
    
    async def _extract_text(self, file_path: str, filename: str) -> str:
        """Extract text content from various file formats"""
        
        file_extension = Path(filename).suffix.lower()
        
        try:
            if file_extension == '.pdf':
                return await self._extract_pdf_text(file_path)
            elif file_extension == '.docx':
                return await self._extract_docx_text(file_path)
            elif file_extension == '.txt':
                return await self._extract_txt_text(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
                
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {e}")
            raise
    
    async def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text_content = ""
        
        def extract_sync():
            nonlocal text_content
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num + 1}: {e}")
        
        # Run in thread pool to avoid blocking
        await asyncio.get_event_loop().run_in_executor(None, extract_sync)
        return text_content
    
    async def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        text_content = ""
        
        def extract_sync():
            nonlocal text_content
            doc = Document(file_path)
            paragraphs = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    paragraphs.append(paragraph.text)
            text_content = "\n".join(paragraphs)
        
        await asyncio.get_event_loop().run_in_executor(None, extract_sync)
        return text_content
    
    async def _extract_txt_text(self, file_path: str) -> str:
        """Extract text from TXT file"""
        def extract_sync():
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
        
        return await asyncio.get_event_loop().run_in_executor(None, extract_sync)
    
    def _split_text(self, text: str) -> List[str]:
        """Simple text splitter with overlap"""
        chunks = []
        text_length = len(text)
        
        if text_length <= self.chunk_size:
            return [text]
        
        start = 0
        while start < text_length:
            end = start + self.chunk_size
            
            # Try to break at sentence or paragraph boundaries
            if end < text_length:
                # Look for sentence endings
                for i in range(end, max(start + self.chunk_size // 2, end - 200), -1):
                    if text[i] in '.!?\n':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start >= text_length:
                break
        
        return chunks
    
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using OpenAI"""
        try:
            # Generate embeddings in batches to avoid rate limits
            batch_size = 100
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                def generate_sync():
                    response = self.openai_client.embeddings.create(
                        model=settings.rag_embedding_model,
                        input=batch
                    )
                    return [embedding.embedding for embedding in response.data]
                
                batch_embeddings = await asyncio.get_event_loop().run_in_executor(None, generate_sync)
                all_embeddings.extend(batch_embeddings)
                
                logger.info(f"Generated embeddings for batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete all chunks for a document from ChromaDB"""
        try:
            # Get all chunk IDs for this document
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
                return True
            else:
                logger.warning(f"No chunks found for document {document_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the document collection"""
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection_name
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"total_chunks": 0, "collection_name": self.collection_name}

# Global instance
document_processor = DocumentProcessor()
