import openai
from datetime import datetime
from ..config import settings

async def generate_suggestion(call_id: str, customer_message: str) -> dict:
    """
    Generates a suggestion for the agent based on the customer's message.
    """
    try:
        # Create a new client instance with the current API key
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Create a prompt for the AI assistant to generate suggestions
        prompt = f"""
        You are an AI assistant helping customer service agents.
        A customer just said: "{customer_message}"
        
        Provide a helpful suggestion for the agent on how to respond to this customer message.
        Be specific, actionable, and considerate of the customer's needs.
        """
        
        # Call OpenAI API to generate a response using the new API format
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150
        )
        
        suggestion_text = response.choices[0].message.content.strip()
        
        return {
            "suggestion": suggestion_text,
            "confidence": 0.9,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"Error generating AI suggestion: {e}")
        # Return a fallback suggestion if API call fails
        return {
            "suggestion": f"Consider responding to: '{customer_message}'",
            "confidence": 0.5,
            "timestamp": datetime.utcnow().isoformat()
        }