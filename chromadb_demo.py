import chromadb
import requests
import time
import sys

def check_chromadb_status():
    """Check if ChromaDB is running by calling the heartbeat endpoint"""
    try:
        response = requests.get("http://localhost:8000/api/v2/heartbeat")
        if response.status_code == 200:
            print("✓ ChromaDB is running")
            return True
        else:
            print("✗ ChromaDB is not responding correctly")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to connect to ChromaDB: {e}")
        return False

def list_collections():
    """List all existing collections in ChromaDB"""
    # First check if ChromaDB is running
    print("Checking ChromaDB status...")
    if not check_chromadb_status():
        print("Please ensure ChromaDB is running before executing this script.")
        return

    print("\nConnecting to ChromaDB...")
    try:
        # Connect to the running ChromaDB instance
        client = chromadb.HttpClient(host="localhost", port=8000)
        
        # List existing collections
        print("\nExisting collections:")
        collections = client.list_collections()
        if collections:
            for collection in collections:
                print(f"  - {collection.name}")
        else:
            print("  No collections found.")
        
    except Exception as e:
        print(f"Error: {e}")

def create_collection(collection_name):
    """Create a collection with the specified name and add sample documents"""
    # First check if ChromaDB is running
    print("Checking ChromaDB status...")
    if not check_chromadb_status():
        print("Please ensure ChromaDB is running before executing this script.")
        return

    print("\nConnecting to ChromaDB...")
    try:
        # Connect to the running ChromaDB instance
        client = chromadb.HttpClient(host="localhost", port=8000)
        
        # Check if collection already exists
        collections = client.list_collections()
        if any(collection.name == collection_name for collection in collections):
            print(f"Collection '{collection_name}' already exists.")
            return
        
        # Create a new collection with the specified name
        print(f"\nCreating collection: {collection_name}")
        collection = client.create_collection(name=collection_name)
        print(f"✓ Created collection: {collection.name}")
        
        # Add documents to the collection
        print("\nAdding documents to the collection...")
        collection.add(
            documents=[
                "This is a test document about artificial intelligence.",
                "Machine learning is a subset of AI that focuses on algorithms.",
                "Natural language processing helps computers understand human language.",
                "Computer vision enables machines to interpret visual information.",
                "Deep learning uses neural networks with multiple layers."
            ],
            ids=["doc1", "doc2", "doc3", "doc4", "doc5"],
            metadatas=[
                {"category": "AI", "type": "general"},
                {"category": "ML", "type": "technique"},
                {"category": "NLP", "type": "application"},
                {"category": "CV", "type": "application"},
                {"category": "DL", "type": "technique"}
            ]
        )
        print("✓ Added 5 documents to the collection")
        
        # Get collection stats
        count = collection.count()
        print(f"Total documents in collection: {count}")
        
        print(f"\nCollection '{collection_name}' has been created and will persist.")
        print("Use 'python chromadb_demo.py delete {collection_name}' to remove it later.")
        
    except Exception as e:
        print(f"Error: {e}")

def delete_collection(collection_name):
    """Delete a collection with the specified name"""
    # First check if ChromaDB is running
    print("Checking ChromaDB status...")
    if not check_chromadb_status():
        print("Please ensure ChromaDB is running before executing this script.")
        return

    print("\nConnecting to ChromaDB...")
    try:
        # Connect to the running ChromaDB instance
        client = chromadb.HttpClient(host="localhost", port=8000)
        
        # Check if collection exists
        collections = client.list_collections()
        if not any(collection.name == collection_name for collection in collections):
            print(f"Collection '{collection_name}' does not exist.")
            return
        
        # Delete the collection
        print(f"\nDeleting collection: {collection_name}")
        client.delete_collection(name=collection_name)
        print(f"✓ Deleted collection: {collection_name}")
        
    except Exception as e:
        print(f"Error: {e}")

def run_demo():
    """Run the full ChromaDB demo"""
    # First check if ChromaDB is running
    print("Checking ChromaDB status...")
    if not check_chromadb_status():
        print("Please ensure ChromaDB is running before executing this script.")
        return

    print("\nConnecting to ChromaDB...")
    try:
        # Connect to the running ChromaDB instance
        client = chromadb.HttpClient(host="localhost", port=8000)
        
        # List existing collections
        print("\nExisting collections:")
        collections = client.list_collections()
        for collection in collections:
            print(f"  - {collection.name}")
        
        # Create a new collection
        print("\nCreating a new collection...")
        collection = client.create_collection(name=f"demo_collection_{int(time.time())}")
        print(f"✓ Created collection: {collection.name}")
        
        # Add documents to the collection
        print("\nAdding documents to the collection...")
        collection.add(
            documents=[
                "This is a test document about artificial intelligence.",
                "Machine learning is a subset of AI that focuses on algorithms.",
                "Natural language processing helps computers understand human language.",
                "Computer vision enables machines to interpret visual information.",
                "Deep learning uses neural networks with multiple layers."
            ],
            ids=["doc1", "doc2", "doc3", "doc4", "doc5"],
            metadatas=[
                {"category": "AI", "type": "general"},
                {"category": "ML", "type": "technique"},
                {"category": "NLP", "type": "application"},
                {"category": "CV", "type": "application"},
                {"category": "DL", "type": "technique"}
            ]
        )
        print("✓ Added 5 documents to the collection")
        
        # Query the collection
        print("\nQuerying the collection for 'AI and machine learning'...")
        results = collection.query(
            query_texts=["AI and machine learning"],
            n_results=3
        )
        
        print("\nQuery results:")
        for i, (doc, metadata, id) in enumerate(zip(
            results['documents'][0], 
            results['metadatas'][0], 
            results['ids'][0]
        )):
            print(f"  {i+1}. ID: {id}")
            print(f"     Document: {doc}")
            print(f"     Metadata: {metadata}")
            print()
        
        # Get collection stats
        count = collection.count()
        print(f"Total documents in collection: {count}")
        
        # Clean up - delete the collection
        print("Cleaning up...")
        client.delete_collection(name=collection.name)
        print(f"✓ Deleted collection: {collection.name}")
        
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Main function that handles command line arguments"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "list":
            list_collections()
        elif command == "create" and len(sys.argv) > 2:
            create_collection(sys.argv[2])
        elif command == "delete" and len(sys.argv) > 2:
            delete_collection(sys.argv[2])
        else:
            print("Usage:")
            print("  python chromadb_demo.py          # Run full demo")
            print("  python chromadb_demo.py list     # List all collections")
            print("  python chromadb_demo.py create <name>  # Create a collection with specified name")
            print("  python chromadb_demo.py delete <name>  # Delete a collection by name")
    else:
        run_demo()

if __name__ == "__main__":
    main()