# Add Curated RAG Pack with Citations

## Why
The assistant must provide accurate, evidence-based advice grounded in trusted sources. Without RAG, responses could be hallucinated or inaccurate. Citations are essential for parent trust and accountability.

## What Changes
- Create RAG ingestion pipeline (`rag/ingest.py`)
- Build vector index from curated sources (`rag/index.json`)
- Implement retrieval helper function
- Add citation display in frontend UI (badges/links)
- Ensure ≥90% of responses include ≥1 citation in sampled sessions

## Impact
- Affected specs: New capability `rag-retrieval`
- Affected code:
  - `rag/ingest.py` - Document ingestion and vectorization
  - `rag/index.json` - Vector index storage
  - `rag/sources/` - Curated source documents
  - `backend/app/rag.py` - Retrieval functions
  - `backend/app/api/websocket.py` - Integration with LLM
  - `frontend/src/components/CitationBadge.tsx` - Citation UI component
  - `frontend/src/app/coach/chat/page.tsx` - Display citations in messages

