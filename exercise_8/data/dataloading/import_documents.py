import redis
import json
import uuid
import os

def import_documents():
    """
    Import sample documents into Redis for the Exercise 8 application
    """
    # Connect to Redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        r = redis.from_url(redis_url, decode_responses=True)
        r.ping()
        print("[SUCCESS] Successfully connected to Redis")
    except Exception as e:
        print(f"[ERROR] Failed to connect to Redis: {e}")
        print("Make sure Redis is running (try: docker-compose up redis)")
        return

    # Read the sample NDA document
    try:
        with open("sample_nda.md", "r", encoding="utf-8") as f:
            nda_content = f.read()
    except FileNotFoundError:
        print("[ERROR] sample_nda.md file not found")
        return

    # Parse document into clauses (simplified parsing)
    lines = nda_content.split('\n')
    clauses = []
    current_clause = {"id": "", "heading": "", "text": ""}
    clause_counter = 1

    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('#') and any(c.isalpha() for c in line):  # Header line
            # If we were building a previous clause, save it
            if current_clause["heading"]:
                clauses.append({
                    "id": f"clause_{clause_counter - 1}",
                    "heading": current_clause["heading"],
                    "text": current_clause["text"].strip()
                })
            
            # Start a new clause
            heading = line.replace('#', '').strip()
            current_clause = {
                "id": f"clause_{clause_counter}",
                "heading": heading,
                "text": heading + "\n"
            }
            clause_counter += 1
        elif line:  # Non-empty line, add to current clause
            if current_clause["heading"]:  # Make sure we have a heading
                current_clause["text"] += line + "\n"

    # Don't forget the last clause
    if current_clause["heading"]:
        clauses.append({
            "id": f"clause_{clause_counter - 1}",
            "heading": current_clause["heading"],
            "text": current_clause["text"].strip()
        })

    # Create document data
    doc_data = {
        "name": "Sample_NDA.md",
        "content": nda_content,
        "clauses": clauses
    }

    # Store document in Redis
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    doc_key = f"doc:{doc_id}"
    
    r.set(doc_key, json.dumps(doc_data))
    
    print(f"[INFO] Added document '{doc_data['name']}' with ID: {doc_id}")
    print(f"[INFO] Document contains {len(clauses)} clauses")

    # Verify the import by listing documents
    print("\n[INFO] Verifying imported documents...")
    doc_keys = r.keys("doc:*")
    print(f"Total documents in Redis: {len(doc_keys)}")
    
    for key in doc_keys:
        doc_data = json.loads(r.get(key))
        print(f"  - {doc_data['name']} ({key}) - {len(doc_data.get('clauses', []))} clauses")

    print("\n[SUCCESS] Document import completed successfully!")

if __name__ == "__main__":
    import_documents()