"""
Simple keyword-based retrieval for demo purposes.
For production, replace with vector embeddings (OpenAI, Pinecone, etc.)
"""

from typing import List, Dict


# Curated knowledge base with citations
KNOWLEDGE_BASE = {
    'bedtime': {
        'source': 'AAP - Healthy Sleep Habits',
        'url': 'https://www.healthychildren.org/English/healthy-living/sleep',
        'content': '''Consistent bedtime routines help children sleep better. The American Academy of Pediatrics recommends:
        1) Start the routine 30 minutes before bedtime
        2) Include calming activities like reading or quiet play
        3) Dim the lights and reduce stimulation
        4) Keep the routine consistent every night
        Research shows that children with regular bedtime routines fall asleep faster and sleep longer.'''
    },
    'screen_time': {
        'source': 'AAP - Media Guidelines 2023',
        'url': 'https://www.healthychildren.org/English/media',
        'content': '''The AAP recommends screen time limits based on age:
        - Under 18 months: Avoid screens except video chatting
        - 18-24 months: High-quality programming only, watch together
        - 2-5 years: Limit to 1 hour per day of high-quality content
        - 6+ years: Consistent limits that don't interfere with sleep, exercise, or social time
        Co-viewing and discussing content is important at all ages.'''
    },
    'tantrums': {
        'source': 'CDC - Positive Parenting Tips',
        'url': 'https://www.cdc.gov/parents/essentials',
        'content': '''Tantrums are normal in young children. The CDC recommends:
        1) Stay calm yourself - children model your behavior
        2) Validate their feelings: "I see you're upset"
        3) Set clear, consistent boundaries
        4) Don't give in to demands made during tantrums
        5) Once calm, talk about better ways to express feelings
        Most tantrums last 2-5 minutes. Staying calm helps them pass faster.'''
    },
    'picky_eating': {
        'source': 'AAP - Nutrition Guidelines',
        'url': 'https://www.healthychildren.org/English/healthy-living/nutrition',
        'content': '''Picky eating is common in toddlers and preschoolers. AAP advice:
        - Offer new foods 10-15 times before giving up
        - Serve small portions to avoid overwhelming
        - Let children serve themselves when possible
        - Make mealtimes pleasant, not battles
        - Model healthy eating yourself
        Most children outgrow picky eating by age 5-6 with consistent, low-pressure exposure.'''
    },
    'sibling_conflict': {
        'source': 'CDC - Sibling Relationships',
        'url': 'https://www.cdc.gov/parents',
        'content': '''Sibling conflict is normal. Strategies that help:
        1) Don't always intervene - let them work it out when safe
        2) Teach problem-solving skills
        3) Avoid comparing siblings
        4) Give each child individual attention
        5) Praise cooperative behavior
        Children learn negotiation and conflict resolution through sibling interactions.'''
    },
    'praise': {
        'source': 'CDC - Positive Parenting',
        'url': 'https://www.cdc.gov/parents/essentials',
        'content': '''Effective praise focuses on effort, not just results:
        - "You worked really hard on that" rather than "You're so smart"
        - Be specific: "I noticed you shared your toy"
        - Praise immediately after the behavior
        - Use a warm, genuine tone
        - Balance praise with other positive attention
        Process-focused praise builds resilience and motivation.'''
    },
    'discipline': {
        'source': 'AAP - Effective Discipline',
        'url': 'https://www.healthychildren.org/English/family-life/family-dynamics/communication-discipline',
        'content': '''The AAP recommends positive discipline approaches:
        - Set clear, age-appropriate expectations
        - Use natural consequences when possible
        - Time-outs: 1 minute per year of age
        - Avoid physical punishment
        - Redirect to positive behaviors
        - Be consistent between caregivers
        Discipline teaches self-control, not just compliance.'''
    }
}


def retrieve_context(query: str, max_results: int = 2) -> List[Dict]:
    """
    Retrieve relevant content based on keyword matching.
    
    Args:
        query: The parent's question
        max_results: Maximum number of results to return
        
    Returns:
        List of dicts with 'source', 'url', and 'content'
    """
    query_lower = query.lower()
    results = []
    
    # Keywords to topic mapping
    topic_keywords = {
        'bedtime': ['bedtime', 'sleep', 'routine', 'bed time', 'sleeping', 'nap'],
        'screen_time': ['screen', 'tv', 'television', 'ipad', 'tablet', 'phone', 'video', 'youtube'],
        'tantrums': ['tantrum', 'meltdown', 'crying', 'screaming', 'upset', 'angry'],
        'picky_eating': ['picky', 'eat', 'eating', 'food', 'meal', 'vegetable', 'nutrition'],
        'sibling_conflict': ['sibling', 'brother', 'sister', 'fight', 'arguing', 'sharing', 'jealous'],
        'praise': ['praise', 'compliment', 'reward', 'encourage', 'motivation', 'positive'],
        'discipline': ['discipline', 'punishment', 'consequence', 'behavior', 'misbehave', 'listen']
    }
    
    # Find matching topics
    matched_topics = []
    for topic, keywords in topic_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            matched_topics.append(topic)
    
    # Get documents for matched topics
    for topic in matched_topics[:max_results]:
        if topic in KNOWLEDGE_BASE:
            results.append(KNOWLEDGE_BASE[topic])
    
    return results


def format_with_citations(advice: str, citations: List[Dict]) -> Dict:
    """
    Format advice with citations for frontend display.
    
    Args:
        advice: The advice text
        citations: List of citation dicts
        
    Returns:
        Dict with 'text' and 'citations' keys
    """
    return {
        'text': advice,
        'citations': [
            {
                'source': cite['source'],
                'url': cite['url']
            }
            for cite in citations
        ]
    }


def get_advice_with_rag(question: str) -> Dict:
    """
    Generate advice using RAG (simplified for demo).
    
    Args:
        question: Parent's question
        
    Returns:
        Dict with advice text and citations
    """
    # Retrieve relevant context
    citations = retrieve_context(question, max_results=2)
    
    if not citations:
        # No specific guidance found
        return {
            'text': "I don't have specific guidance on that topic in my knowledge base. Could you rephrase your question or ask about common topics like bedtime, screen time, tantrums, or picky eating?",
            'citations': []
        }
    
    # For demo: Use the first citation's content as advice
    # In production: Send context to LLM for generation
    primary_source = citations[0]
    advice = f"Based on {primary_source['source']}: {primary_source['content']}"
    
    return format_with_citations(advice, citations)


# Export for easy import
__all__ = ['retrieve_context', 'get_advice_with_rag', 'format_with_citations', 'KNOWLEDGE_BASE']

