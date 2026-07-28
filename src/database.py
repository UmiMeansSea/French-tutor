import os
import glob
import sqlite3
import chromadb

def get_sqlite_path():
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "tutor_data.db")

def init_sqlite_db():
    db_path = get_sqlite_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Profile table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY DEFAULT 1,
            level TEXT DEFAULT 'A1',
            xp INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Vocabulary Vault table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary_vault (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE,
            translation TEXT,
            cefr_level TEXT DEFAULT 'A1',
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Mentor Notepad table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notepad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            mentor_name TEXT,
            user_input TEXT,
            correction TEXT,
            rule TEXT
        )
    """)
    
    cursor.execute("INSERT OR IGNORE INTO user_profile (id, level, xp, streak) VALUES (1, 'A1', 0, 0)")
    conn.commit()
    conn.close()

def save_notepad_entry(mentor_name, user_input, correction, rule="Grammar Correction"):
    if not correction or not str(correction).strip():
        return
    db_path = get_sqlite_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO notepad (mentor_name, user_input, correction, rule) VALUES (?, ?, ?, ?)",
            (mentor_name.strip(), user_input.strip(), correction.strip(), rule.strip())
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

def get_notepad_entries():
    db_path = get_sqlite_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp, mentor_name, user_input, correction, rule FROM notepad ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def save_vault_word(word, translation="N/A", cefr_level="A1"):
    if not word or not str(word).strip():
        return
    db_path = get_sqlite_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO vocabulary_vault (word, translation, cefr_level) VALUES (?, ?, ?)",
            (word.strip(), translation.strip(), cefr_level.strip())
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

def get_vault_words():
    db_path = get_sqlite_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT word, translation, cefr_level, date_added FROM vocabulary_vault ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def sync_sqlite_profile(level, xp, streak):
    db_path = get_sqlite_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE user_profile SET level = ?, xp = ?, streak = ?, last_active = CURRENT_TIMESTAMP WHERE id = 1",
        (level, xp, streak)
    )
    conn.commit()
    conn.close()

def get_chroma_collection():
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
        
        try:
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
        except Exception:
            print("[Warning: Could not connect to embedding server. Skipping cloud ingestion and using local cache.]")
            return
    print("Database updated successfully!\n")

def auto_ingest_knowledge(client, collection_db):
    init_sqlite_db()
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "knowledge_docs")
    if not os.path.exists(docs_dir):
        return
    for ext in ("*.txt", "*.md"):
        for filepath in glob.glob(os.path.join(docs_dir, ext)):
            try:
                load_document_to_db(filepath, client, collection_db)
            except Exception:
                print(f"[Warning: Failed to ingest {os.path.basename(filepath)}. Using local cache.]")
