import os
import glob
import chromadb

def get_chroma_collection():
    # Ensure it's saved in the project root's db/chroma_db folder
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "chroma_db")
    chroma_client = chromadb.PersistentClient(path=db_path)
    return chroma_client.get_or_create_collection(name="french_tutor_db")

def load_document_to_db(filepath, client, collection_db):
    print(f"Reading file: {filepath}...")
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found.")
        return
        
    with open(filepath, 'r', encoding='utf-8') as file:
        raw_text = file.read()
        
    chunks = raw_text.split('\n\n')
    chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
    
    if not chunks:
        print("No grammar rules found.")
        return
        
    print(f"Found {len(chunks)} grammar rules. Embedding and saving to database...")
    
    for index, chunk in enumerate(chunks):
        chunk_id = f"{os.path.basename(filepath)}_chunk_{index}"
        
        embed_response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=chunk
        )
        vector = embed_response.embeddings[0].values
        
        collection_db.upsert(
            ids=[chunk_id],
            embeddings=[vector],
            documents=[chunk],
            metadatas=[{"source": filepath}]
        )
    print("Database updated successfully!\n")

def auto_ingest_knowledge(client, collection_db):
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "knowledge_docs")
    if not os.path.exists(docs_dir):
        return
    for ext in ("*.txt", "*.md"):
        for filepath in glob.glob(os.path.join(docs_dir, ext)):
            load_document_to_db(filepath, client, collection_db)
