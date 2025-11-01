# Implementation Tasks

## 1. Source Curation
- [ ] 1.1 Collect authoritative sources (AAP, CDC, peer-reviewed journals)
- [ ] 1.2 Store documents in `rag/sources/` directory
- [ ] 1.3 Add metadata (title, author, URL, publication date)

## 2. Ingestion Pipeline
- [ ] 2.1 Create `rag/ingest.py` script
- [ ] 2.2 Implement document chunking strategy (overlap, size)
- [ ] 2.3 Generate embeddings using OpenAI embeddings API
- [ ] 2.4 Build vector index and save to `rag/index.json`
- [ ] 2.5 Add CLI command to re-index sources

## 3. Retrieval Backend
- [ ] 3.1 Create `backend/app/rag.py` module
- [ ] 3.2 Implement `retrieve_context()` function
- [ ] 3.3 Add similarity search with top-k results
- [ ] 3.4 Format retrieved chunks with citation metadata
- [ ] 3.5 Integrate retrieval into WebSocket message handler

## 4. LLM Integration
- [ ] 4.1 Modify prompt to include retrieved context
- [ ] 4.2 Instruct LLM to cite sources in responses
- [ ] 4.3 Parse LLM output to extract citation references
- [ ] 4.4 Return citations along with advice text

## 5. Frontend Display
- [ ] 5.1 Create `CitationBadge` component
- [ ] 5.2 Display citation badges inline or at end of messages
- [ ] 5.3 Make citations clickable (open source URL)
- [ ] 5.4 Style citations clearly and accessibly

## 6. Validation
- [ ] 6.1 Sample 10 chat sessions
- [ ] 6.2 Count responses with ≥1 citation
- [ ] 6.3 Assert ≥90% citation rate
- [ ] 6.4 Manual review for citation relevance and accuracy

