#!/usr/bin/env python3
"""
Script to update existing Q&A pairs with embeddings
Run this script to add embeddings to Q&A pairs that were created without them
"""

import asyncio
import logging
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import init_database, close_database, execute_raw_query, execute_raw_command
from app.services.vector_service import vector_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def update_qa_embeddings():
    """Update all Q&A pairs that don't have embeddings"""
    try:
        # Initialize database
        await init_database()
        logger.info("Database initialized successfully")
        
        # Initialize vector service
        await vector_service.initialize()
        logger.info("Vector service initialized successfully")
        
        # Get all Q&A pairs without embeddings
        qa_pairs = await execute_raw_query("""
            SELECT id, question, answer 
            FROM qa_pairs 
            WHERE status = 'active' 
            AND (question_embedding IS NULL OR answer_embedding IS NULL)
        """)
        
        logger.info(f"Found {len(qa_pairs)} Q&A pairs without embeddings")
        
        if not qa_pairs:
            logger.info("All Q&A pairs already have embeddings")
            return
        
        # Update each Q&A pair with embeddings
        for qa_pair in qa_pairs:
            qa_id = qa_pair['id']
            question = qa_pair['question']
            answer = qa_pair['answer']
            
            logger.info(f"Updating embeddings for Q&A pair {qa_id}")
            
            try:
                # Generate embeddings
                question_embedding = await vector_service.generate_embedding(question)
                answer_embedding = await vector_service.generate_embedding(answer)
                
                # Convert embeddings to pgvector format (string representation)
                question_embedding_str = '[' + ','.join(map(str, question_embedding)) + ']'
                answer_embedding_str = '[' + ','.join(map(str, answer_embedding)) + ']'
                
                # Update the database
                await execute_raw_command("""
                    UPDATE qa_pairs
                    SET question_embedding = $1::vector, answer_embedding = $2::vector
                    WHERE id = $3
                """, question_embedding_str, answer_embedding_str, qa_id)
                
                logger.info(f"Successfully updated embeddings for Q&A pair {qa_id}")
                
            except Exception as e:
                logger.error(f"Failed to update embeddings for Q&A pair {qa_id}: {e}")
        
        logger.info("Finished updating Q&A embeddings")
        
    except Exception as e:
        logger.error(f"Error updating Q&A embeddings: {e}")
        raise
    finally:
        await close_database()

if __name__ == "__main__":
    asyncio.run(update_qa_embeddings())
