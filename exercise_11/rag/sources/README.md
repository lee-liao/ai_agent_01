# RAG Knowledge Sources

This directory contains curated parenting advice sources for the Child Growth Assistant.

## Current Sources (Demo - Embedded in Code)

For the quick demo, sources are embedded in `rag/simple_retrieval.py`:

1. **AAP - Healthy Sleep Habits**
   - Topic: Bedtime routines
   - Source: https://www.healthychildren.org/English/healthy-living/sleep

2. **AAP - Media Guidelines 2023**
   - Topic: Screen time limits by age
   - Source: https://www.healthychildren.org/English/media

3. **CDC - Positive Parenting Tips**
   - Topic: Managing tantrums
   - Source: https://www.cdc.gov/parents/essentials

4. **AAP - Nutrition Guidelines**
   - Topic: Picky eating strategies
   - Source: https://www.healthychildren.org/English/healthy-living/nutrition

5. **CDC - Sibling Relationships**
   - Topic: Sibling conflict resolution
   - Source: https://www.cdc.gov/parents

6. **CDC - Positive Parenting**
   - Topic: Effective praise and motivation
   - Source: https://www.cdc.gov/parents/essentials

7. **AAP - Effective Discipline**
   - Topic: Age-appropriate discipline strategies
   - Source: https://www.healthychildren.org/English/family-life/family-dynamics/communication-discipline

## Future Improvements

For production, replace with:

1. **Vector Embeddings**:
   - Use OpenAI embeddings or similar
   - Store in Pinecone, Weaviate, or local FAISS

2. **Document Ingestion Pipeline**:
   - PDF/web scraping from AAP, CDC, peer-reviewed journals
   - Chunking strategy (e.g., 500 tokens with 50 token overlap)
   - Metadata tracking (title, author, date, URL)

3. **Semantic Search**:
   - Embed queries and documents
   - Cosine similarity matching
   - Top-k retrieval with relevance scoring

4. **Citation Tracking**:
   - Maintain source attribution
   - Version control for source updates
   - Automatic link verification

## Adding New Sources

To add sources for demo:
1. Edit `rag/simple_retrieval.py`
2. Add entry to `KNOWLEDGE_BASE` dict
3. Add keywords to `topic_keywords` mapping
4. Test retrieval with sample questions

