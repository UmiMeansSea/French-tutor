import os
import glob
import sqlite3
import chromadb

import hashlib

def get_sqlite_path():
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "tutor_data.db")

def init_sqlite_db():
    db_path = get_sqlite_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Cleaned User Profile table (focused on language learning identity)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY DEFAULT 1,
            name TEXT DEFAULT 'Learner',
            hometown TEXT DEFAULT '',
            profile_completed INTEGER DEFAULT 0,
            level TEXT DEFAULT 'A1',
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
            rule TEXT,
            category TEXT DEFAULT 'General'
        )
    """)
    
    cursor.execute("INSERT OR IGNORE INTO user_profile (id, name, hometown, profile_completed, level) VALUES (1, 'Learner', '', 0, 'A1')")
    conn.commit()
    conn.close()

def get_user_profile_data():
    db_path = get_sqlite_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, hometown, profile_completed, level FROM user_profile WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "name": row[0] or "Learner",
            "hometown": row[1] or "",
            "profile_completed": bool(row[2]),
            "level": row[3] or "A1"
        }
    return {"name": "Learner", "hometown": "", "profile_completed": False, "level": "A1"}

def save_user_profile_data(name, hometown="", profile_completed=1):
    db_path = get_sqlite_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE user_profile SET name = ?, hometown = ?, profile_completed = ?, last_active = CURRENT_TIMESTAMP WHERE id = 1",
        (name.strip(), hometown.strip(), 1 if profile_completed else 0)
    )
    conn.commit()
    conn.close()

def save_notepad_entry(mentor_name, user_input, correction, rule="Grammar Correction", category="General"):
    if not correction or not str(correction).strip():
        return
    db_path = get_sqlite_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO notepad (mentor_name, user_input, correction, rule, category) VALUES (?, ?, ?, ?, ?)",
            (mentor_name.strip(), user_input.strip(), correction.strip(), rule.strip(), category.strip())
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

def get_top_error_category():
    db_path = get_sqlite_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT category, COUNT(*) as count FROM notepad WHERE category != 'General' GROUP BY category ORDER BY count DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
    except Exception:
        pass
    return None

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

def sync_sqlite_profile(level):
    db_path = get_sqlite_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE user_profile SET level = ?, last_active = CURRENT_TIMESTAMP WHERE id = 1",
        (level,)
    )
    conn.commit()
    conn.close()

def get_chroma_collection():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "chroma_db")
    chroma_client = chromadb.PersistentClient(path=db_path)
    return chroma_client.get_or_create_collection(name="french_tutor_db")

def compute_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def load_document_to_db(filepath, client, collection_db):
    if not os.path.exists(filepath):
        return

    current_hash = compute_file_hash(filepath)
    doc_id_prefix = os.path.basename(filepath)

    # Check if existing chunks in ChromaDB match current file hash
    existing = collection_db.get(where={"source": filepath}, limit=1)
    if existing and existing.get('metadatas') and len(existing['metadatas']) > 0:
        cached_hash = existing['metadatas'][0].get('hash')
        if cached_hash == current_hash:
            # File unchanged, skip embedding API calls
            return

    print(f"Ingesting updated knowledge document: {os.path.basename(filepath)}...")
    with open(filepath, 'r', encoding='utf-8') as file:
        raw_text = file.read()
        
    chunks = raw_text.split('\n\n')
    chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
    if not chunks:
        return
        
    for index, chunk in enumerate(chunks):
        chunk_id = f"{doc_id_prefix}_chunk_{index}"
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
                metadatas=[{"source": filepath, "hash": current_hash}]
            )
        except Exception:
            return

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
                pass

