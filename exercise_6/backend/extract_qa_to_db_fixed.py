import asyncio
import json
import logging
import os
import re
import uuid
from typing import List, Dict, Optional

import asyncpg
import pdfplumber
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QAPairExtractor:
    """Extract Q&A pairs from PDF documents."""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def extract_qa_from_pdf(self, pdf_path: str) -> List[Dict[str, str]]:
        """Extract Q&A pairs from a PDF file."""
        qa_pairs = []
        current_question = None
        current_answer_lines = []

        if not os.path.exists(pdf_path):
            logger.error(f"Error: PDF file not found at {pdf_path}")
            return []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        lines = text.split('\n')
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue

                            # Ignore lines that are just numbered titles (e.g., "1. Why RAG...")
                            if re.match(r'^\d+\.\s', line):
                                continue

                            if line.startswith("Ask:"):
                                if current_question and current_answer_lines:
                                    qa_pairs.append({
                                        "question": current_question,
                                        "answer": " ".join(current_answer_lines).strip()
                                    })
                                current_question = line[len("Ask:"):].strip()
                                current_answer_lines = []
                            elif line.startswith("Strong answers:"):
                                if current_question:
                                    current_answer_lines.append(line[len("Strong answers:"):].strip())
                            elif current_question: 
                                current_answer_lines.append(line)

            if current_question and current_answer_lines:
                qa_pairs.append({
                    "question": current_question,
                    "answer": " ".join(current_answer_lines).strip()
                })
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return []

        return qa_pairs
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI."""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.embeddings.create(
                    model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
                    input=text.strip()
                )
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise


class QAPairDatabase:
    """Handle database operations for Q&A pairs."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
    
    async def connect(self):
        """Establish database connection pool."""
        try:
            # Convert SQLAlchemy-style URL to asyncpg format
            asyncpg_url = self.database_url.replace("postgresql+asyncpg://", "postgresql://")
            self.pool = await asyncpg.create_pool(
                asyncpg_url,
                min_size=2,
                max_size=10,
                command_timeout=30,
            )
            logger.info("Database connection pool established successfully")
            
            # Verify pgvector extension
            async with self.pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                )
                if result:
                    logger.info("pgvector extension is available")
                else:
                    logger.error("pgvector extension not found - embeddings will not work")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def ensure_knowledge_base(self, name: str = "Default Knowledge Base") -> str:
        """Ensure a knowledge base exists and return its ID."""
        async with self.pool.acquire() as conn:
            # Try to get existing knowledge base
            kb_id = await conn.fetchval(
                "SELECT id FROM knowledge_bases WHERE name = $1",
                name
            )
            
            if kb_id:
                return str(kb_id)
            
            # Create new knowledge base
            kb_id = await conn.fetchval("""
                INSERT INTO knowledge_bases (name, description, metadata)
                VALUES ($1, $2, $3::jsonb)
                RETURNING id
            """, 
                name, 
                f"Auto-created knowledge base: {name}",
                json.dumps({"created_by": "script", "auto_created": True})
            )
            
            logger.info(f"Created new knowledge base: {name} ({kb_id})")
            return str(kb_id)
    
    async def insert_qa_pair(self, knowledge_base_id: str, question: str, answer: str, 
                            question_embedding: List[float], answer_embedding: List[float],
                            tags: List[str] = None) -> str:
        """Insert a Q&A pair with embeddings into the database."""
        if tags is None:
            tags = []
            
        question_embedding_str = '[' + ','.join(map(str, question_embedding)) + ']'
        answer_embedding_str = '[' + ','.join(map(str, answer_embedding)) + ']'
        
        async with self.pool.acquire() as conn:
            qa_id = await conn.fetchval("""
                INSERT INTO qa_pairs (
                    id, knowledge_base_id, question, answer, 
                    tags, status, question_embedding, answer_embedding
                ) VALUES ($1, $2, $3, $4, $5::text[], 'active', $6::vector, $7::vector)
                RETURNING id
            """, 
                str(uuid.uuid4()), knowledge_base_id, question, answer, 
                tags, question_embedding_str, answer_embedding_str
            )
        
        logger.info(f"Successfully inserted Q&A pair: {qa_id}")
        return str(qa_id)


async def main():
    """Main function to extract Q&A pairs from PDF and store in database."""
    logger.info("🚀 Starting Q&A extraction and database insertion process...")
    
    # Configuration
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://rag_user:rag_password_2024@localhost:5433/rag_chatbot")
    pdf_path = "Top 20 RAG questions.pdf"  # PDF is in the backend directory
    pdf_path = os.path.join(os.path.dirname(__file__), pdf_path)  # Make it absolute
    
    # Validate required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable is not set")
        return
    
    # Create extractor and database instances
    extractor = QAPairExtractor()
    db = QAPairDatabase(database_url)
    
    try:
        # Connect to database
        await db.connect()
        
        # Extract Q&A pairs from PDF
        logger.info(f"Extracting Q&A pairs from {pdf_path}...")
        qa_pairs = extractor.extract_qa_from_pdf(pdf_path)
        
        if not qa_pairs:
            logger.warning("No Q&A pairs extracted from the PDF.")
            return
        
        logger.info(f"Extracted {len(qa_pairs)} Q&A pairs from PDF.")
        
        # Get or create knowledge base
        kb_id = await db.ensure_knowledge_base("RAG Questions PDF")
        
        # Process each Q&A pair
        for i, qa in enumerate(qa_pairs, 1):
            try:
                question = qa['question']
                answer = qa['answer']
                tags = ["rag_top_20", "pdf_extracted"]
                
                logger.info(f"[{i}/{len(qa_pairs)}] Processing Q&A: {question[:50]}...")
                
                # Generate embeddings
                logger.info(f"[{i}/{len(qa_pairs)}] Generating embeddings...")
                question_embedding = await extractor.generate_embedding(question)
                answer_embedding = await extractor.generate_embedding(answer)
                
                # Insert into database
                qa_id = await db.insert_qa_pair(
                    knowledge_base_id=kb_id,
                    question=question,
                    answer=answer,
                    question_embedding=question_embedding,
                    answer_embedding=answer_embedding,
                    tags=tags
                )
                
                logger.info(f"[{i}/{len(qa_pairs)}] Successfully processed Q&A pair {qa_id}")
                
            except Exception as e:
                logger.error(f"[{i}/{len(qa_pairs)}] Failed to process Q&A pair: {e}")
                continue
        
        logger.info("✅ All Q&A pairs processed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Script failed: {e}")
        raise
    finally:
        await db.close()
        logger.info("🛑 Database connection closed.")


if __name__ == "__main__":
    asyncio.run(main())