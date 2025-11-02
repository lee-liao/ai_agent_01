"""
LLM integration for generating parenting advice.
Uses OpenAI API with streaming support.
"""

import openai
from typing import AsyncGenerator
from app.config import settings


# Initialize OpenAI client
def get_openai_client():
    """Get OpenAI client, checking for API key."""
    if not settings.OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY not set. Please create backend/.env with your API key. "
            "Get one at: https://platform.openai.com/api-keys"
        )
    # Create client without custom httpx client to avoid version conflicts
    return openai.AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        timeout=30.0,
        max_retries=2
    )


def build_prompt_with_rag(question: str, rag_context: list) -> list:
    """
    Build prompt messages including RAG context.
    
    Args:
        question: Parent's question
        rag_context: List of retrieved documents with 'source', 'content', 'url'
        
    Returns:
        List of message dicts for OpenAI API
    """
    system_prompt = """You are a supportive parenting coach assistant. Your role is to provide evidence-based advice for parents.

Guidelines:
- Be warm, empathetic, and supportive
- Provide 2-3 specific, actionable steps
- Base advice on the provided research context
- ALWAYS cite sources in your response using [Source Name]
- Keep responses concise and practical
- Focus on positive parenting approaches

Remember: You only provide general parenting guidance. You do NOT provide medical advice, crisis intervention, legal counsel, or therapy."""

    # Add RAG context if available
    if rag_context:
        context_text = "\n\n".join([
            f"Source: {doc['source']}\nContent: {doc['content']}"
            for doc in rag_context
        ])
        system_prompt += f"\n\nResearch Context:\n{context_text}\n\nPlease reference these sources in your response."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]
    
    return messages


async def generate_advice_streaming(
    question: str,
    rag_context: list = None
) -> AsyncGenerator[str, None]:
    """
    Generate parenting advice using OpenAI API with streaming.
    
    Args:
        question: Parent's question
        rag_context: Optional list of RAG documents
        
    Yields:
        String chunks of the response
    """
    messages = build_prompt_with_rag(question, rag_context or [])
    
    try:
        client = get_openai_client()
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            stream=True
        )
        
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    except ValueError as e:
        # API key not set
        yield f"⚠️ OpenAI API not configured. Please set OPENAI_API_KEY in backend/.env file. ({str(e)})"
    except Exception as e:
        # Other errors (rate limit, network, etc.)
        yield f"I'm having trouble connecting to my knowledge base right now. Please try again in a moment. (Error: {str(e)})"


async def generate_advice_non_streaming(
    question: str,
    rag_context: list = None,
    session_id: str = "unknown"
) -> str:
    """
    Generate parenting advice using OpenAI API (non-streaming).
    
    Args:
        question: Parent's question
        rag_context: Optional list of RAG documents
        session_id: Session ID for cost tracking
        
    Returns:
        Complete advice response
    """
    messages = build_prompt_with_rag(question, rag_context or [])
    
    try:
        client = get_openai_client()
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        # Track usage and costs
        from billing.ledger import get_tracker
        tracker = get_tracker()
        tracker.log_usage(
            session_id=session_id,
            model="gpt-3.5-turbo",
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens
        )
        
        return response.choices[0].message.content
        
    except ValueError as e:
        # API key not set
        return f"⚠️ OpenAI API not configured. Please set OPENAI_API_KEY in backend/.env file. Get one at: https://platform.openai.com/api-keys"
    except Exception as e:
        return f"I'm having trouble connecting right now. Please try again in a moment. (Error: {str(e)})"

