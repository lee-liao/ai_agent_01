# Exercise 7 Backend

## Scripts

### Update Q&A Embeddings

If you're seeing issues with the vector service not finding matches for queries that should match existing Q&A pairs, you may need to update the embeddings for those pairs.

This typically happens when Q&A pairs are inserted into the database without embeddings, which are required for vector similarity search to work properly.

To update the embeddings for existing Q&A pairs, run:

```bash
cd backend
python update_qa_embeddings.py
```

This script will:
1. Find all Q&A pairs in the database that don't have embeddings
2. Generate embeddings for the question and answer texts
3. Update the database records with the generated embeddings

After running this script, the vector service should be able to find matches for queries related to content in your Q&A pairs.