## Why
To improve customer service continuity and enable supervisors to review past interactions, conversations should be associated with support tickets. This allows for better tracking, follow-up, and quality assurance.

## What Changes
- Add conversation history storage in database when calls end
- Create association between conversation IDs and support tickets
- Allow agents to view conversation history when handling related tickets
- Store conversation context including audio transcriptions, customer info, and agent responses

## Impact
- Affected specs: ticketing/spec.md, conversation-history/spec.md
- Affected code: backend/app/models.py, backend/app/database.py, backend/app/api/tickets.py, backend/app/api/conversations.py
- New database tables for conversation history and ticket-conversation relationships