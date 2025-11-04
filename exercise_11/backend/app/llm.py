"""
LLM integration for generating parenting advice.
Uses OpenAI API with streaming support.
"""

import time
import openai
from typing import AsyncGenerator, Optional
from app.config import settings
from app.observability import get_tracer


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
    rag_context: list = None,
    session_id: str = "unknown"
) -> AsyncGenerator[str, None]:
    """
    Generate parenting advice using OpenAI API with streaming.
    
    Args:
        question: Parent's question
        rag_context: Optional list of RAG documents
        session_id: Session ID for tracking
        
    Yields:
        String chunks of the response
    """
    tracer = get_tracer()
    start_time = time.time()
    advice_text = ""
    citations_count = len(rag_context) if rag_context else 0
    
    with tracer.start_as_current_span("model.generate_advice_stream") as span:
        # Set initial attributes
        span.set_attribute("model.user_text_length", len(question))
        span.set_attribute("model.session_id", session_id)
        span.set_attribute("model.streaming", True)
        span.set_attribute("model.citations_count", citations_count)
        span.set_attribute("model.has_citations", citations_count > 0)
        
        if rag_context:
            # Set relevance score (for keyword-based, it's 1.0 if matched)
            span.set_attribute("model.relevance_score", 1.0)
        else:
            span.set_attribute("model.relevance_score", 0.0)
        
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
                    content = chunk.choices[0].delta.content
                    advice_text += content
                    yield content
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Set final attributes
            span.set_attribute("model.latency_ms", latency_ms)
            span.set_attribute("model.advice_length", len(advice_text))
            span.set_attribute("model.classification", "SAFE")
                
        except ValueError as e:
            # API key not set
            error_msg = f"⚠️ OpenAI API not configured. Please set OPENAI_API_KEY in backend/.env file. ({str(e)})"
            span.set_attribute("model.classification", "SAFE_FALLBACK")
            span.set_attribute("model.latency_ms", (time.time() - start_time) * 1000)
            yield error_msg
        except Exception as e:
            # Other errors (rate limit, network, etc.)
            error_msg = f"I'm having trouble connecting to my knowledge base right now. Please try again in a moment. (Error: {str(e)})"
            span.set_attribute("model.classification", "SAFE_FALLBACK")
            span.set_attribute("model.latency_ms", (time.time() - start_time) * 1000)
            yield error_msg


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
    tracer = get_tracer()
    start_time = time.time()
    citations_count = len(rag_context) if rag_context else 0
    
    with tracer.start_as_current_span("model.generate_advice") as span:
        # Set initial attributes
        span.set_attribute("model.user_text_length", len(question))
        span.set_attribute("model.session_id", session_id)
        span.set_attribute("model.streaming", False)
        span.set_attribute("model.citations_count", citations_count)
        span.set_attribute("model.has_citations", citations_count > 0)
        
        if rag_context:
            span.set_attribute("model.relevance_score", 1.0)
        else:
            span.set_attribute("model.relevance_score", 0.0)
        
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
            
            advice_text = response.choices[0].message.content
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Set final attributes
            span.set_attribute("model.latency_ms", latency_ms)
            span.set_attribute("model.advice_length", len(advice_text))
            span.set_attribute("model.classification", "SAFE")
            
            return advice_text
            
        except ValueError as e:
            # API key not set
            error_msg = f"⚠️ OpenAI API not configured. Please set OPENAI_API_KEY in backend/.env file. Get one at: https://platform.openai.com/api-keys"
            span.set_attribute("model.classification", "SAFE_FALLBACK")
            span.set_attribute("model.latency_ms", (time.time() - start_time) * 1000)
            return error_msg
        except Exception as e:
            error_msg = f"I'm having trouble connecting right now. Please try again in a moment. (Error: {str(e)})"
            span.set_attribute("model.classification", "SAFE_FALLBACK")
            span.set_attribute("model.latency_ms", (time.time() - start_time) * 1000)
            return error_msg

