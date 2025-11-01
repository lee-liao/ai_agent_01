# RAG Retrieval Capability

## ADDED Requirements

### Requirement: Document Ingestion
The system SHALL ingest curated parenting sources and create a searchable vector index.

#### Scenario: Index AAP guidelines
- **WHEN** administrator runs `python rag/ingest.py`
- **THEN** the system chunks AAP documents
- **AND** generates embeddings for each chunk
- **AND** saves vector index to `rag/index.json`

#### Scenario: Re-indexing after source updates
- **WHEN** new sources are added to `rag/sources/`
- **AND** the ingest script is re-run
- **THEN** the index is updated without losing existing entries

### Requirement: Context Retrieval
The system SHALL retrieve relevant context from the RAG index for each parent question.

#### Scenario: Bedtime question retrieval
- **WHEN** a parent asks "How do I establish a bedtime routine?"
- **THEN** the system retrieves top-3 relevant chunks about bedtime routines
- **AND** includes them in the LLM prompt context

#### Scenario: No relevant context found
- **WHEN** a parent asks a question with no matching sources
- **THEN** the system proceeds without RAG context
- **AND** the LLM response indicates limited specific guidance available

### Requirement: Citation Generation
The system SHALL include citations in responses when using RAG context.

#### Scenario: Response with citation
- **WHEN** the LLM generates advice using RAG context
- **THEN** the response includes inline citations (e.g., "[AAP, 2023]")
- **AND** citation metadata is returned with the message

#### Scenario: Citation metadata
- **WHEN** a citation is included
- **THEN** metadata includes: source title, author, URL, publication date

### Requirement: Citation Display
The frontend SHALL display citations as interactive badges or links.

#### Scenario: Citation badge rendering
- **WHEN** a message contains citations
- **THEN** the UI displays citation badges at the end of the message
- **AND** each badge shows the source name

#### Scenario: Citation click
- **WHEN** a user clicks a citation badge
- **THEN** the source URL opens in a new tab

### Requirement: Citation Rate SLO
In sampled sessions, ≥90% of responses SHALL include at least one citation.

#### Scenario: Citation rate measurement
- **WHEN** 10 chat sessions are sampled
- **THEN** at least 9 sessions have responses with ≥1 citation
- **AND** the citation rate meets the 90% threshold

