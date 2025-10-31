
import asyncio
import logging
import numpy as np
import openai
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path to allow module imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import init_database, close_database, execute_raw_query
from app.services.vector_service import PostgreSQLVectorService
from app.services.rag.llm_service import LLMService

# Initialize services
vector_service = PostgreSQLVectorService()
llm_service = LLMService()

async def get_llm_similarity(question: str, answer: str) -> float:
    """
    Uses an LLM to calculate the semantic similarity between a question and an answer.
    """
    try:
        prompt = f"""
        On a scale from 0.0 to 1.0, how semantically similar are the following question and answer?
        Provide only the numeric score and nothing else.

        Question: {question}
        Answer: {answer}

        Similarity Score:
        """
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: llm_service.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=10
            )
        )
        
        similarity_score_text = response.choices[0].message.content.strip()
        return float(similarity_score_text)
    except Exception as e:
        logger.error(f"Error getting LLM similarity: {e}")
        return 0.0

async def get_vector_similarity(question: str, answer: str) -> float:
    """
    Calculates the cosine similarity between the vector embeddings of a question and an answer.
    """
    try:
        # Generate embeddings for the question and answer
        question_embedding = await vector_service.generate_embedding(question)
        answer_embedding = await vector_service.generate_embedding(answer)

        # Convert to numpy arrays
        vec1 = np.array(question_embedding)
        vec2 = np.array(answer_embedding)

        # Calculate cosine similarity
        cosine_similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        
        return float(cosine_similarity)
    except Exception as e:
        logger.error(f"Error getting vector similarity: {e}")
        return 0.0

async def main():
    """
    Main function to compare QA pair similarities.
    """
    try:
        # Initialize database
        await init_database()
        await vector_service.initialize()

        # 1. Read questions and answers from the qa_pair table
        logger.info("Fetching QA pairs from the database...")
        qa_pairs = await execute_raw_query("SELECT question, answer FROM qa_pairs WHERE status = 'active'")
        
        if not qa_pairs:
            logger.info("No active QA pairs found in the database.")
            return

        results = []
        logger.info(f"Found {len(qa_pairs)} QA pairs. Calculating similarities...")

        for i, pair in enumerate(qa_pairs):
            question = pair['question']
            answer = pair['answer']
            
            logger.info(f"Processing pair {i+1}/{len(qa_pairs)}: '{question[:50]}...'")

            # 2. Get LLM similarity
            llm_sim = await get_llm_similarity(question, answer)
            
            # 3. Get vector similarity
            vec_sim = await get_vector_similarity(question, answer)
            
            results.append({
                "question": question,
                "llm_similarity": llm_sim,
                "vector_similarity": vec_sim
            })

        # 4. List the results for comparison
        # Write results to a text file
        with open("reports/calculate_similarity_result.txt", "w", encoding="utf-8") as f:
            f.write("--- Similarity Comparison Results ---\n")
            f.write(f"{'Question':<60} | {'LLM Similarity':<20} | {'Vector Similarity':<20}\n")
            f.write("-" * 105 + "\n")
            for res in results:
                f.write(f"{res['question'][:58]:<60} | {res['llm_similarity']:<20.4f} | {res['vector_similarity']:<20.4f}\n")
        
        # Also print to console for immediate feedback
        print("\n--- Similarity Comparison Results ---")
        print(f"{'Question':<60} | {'LLM Similarity':<20} | {'Vector Similarity':<20}")
        print("-" * 105)
        for res in results:
            print(f"{res['question'][:58]:<60} | {res['llm_similarity']:<20.4f} | {res['vector_similarity']:<20.4f}")
        
        print(f"\nResults have been saved to 'calculate_similarity_result.txt'")

    except Exception as e:
        logger.error(f"An error occurred in the main process: {e}")
    finally:
        # Close database connections
        await close_database()

if __name__ == "__main__":
    # This script requires the backend environment to be set up,
    # especially the environment variables for database and OpenAI connections.
    # You can run this script from the 'backend' directory.
    # Ensure you have a .env file in the backend directory with the necessary variables.
    
    # To run this, you might need to adjust your PYTHONPATH if you are not running from the root
    # of the project where 'app' is a package.
    # Example from 'backend' folder: python calculate_similarity.py
    
    asyncio.run(main())
