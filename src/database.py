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
            name TEXT DEFAULT 'Learner',
            hometown TEXT DEFAULT '',
            target_goal TEXT DEFAULT '',
            target_university TEXT DEFAULT '',
            target_city TEXT DEFAULT '',
            major TEXT DEFAULT 'General',
            milestone_name TEXT DEFAULT '',
            milestone_date TEXT DEFAULT '',
            profile_completed INTEGER DEFAULT 0,
            level TEXT DEFAULT 'A1',
            xp INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Schema migration check for existing databases
    cursor.execute("PRAGMA table_info(user_profile)")
    columns = [row[1] for row in cursor.fetchall()]
    if "name" not in columns:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN name TEXT DEFAULT 'Learner'")
    if "hometown" not in columns:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN hometown TEXT DEFAULT ''")
    if "target_goal" not in columns:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN target_goal TEXT DEFAULT ''")
    if "target_university" not in columns:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN target_university TEXT DEFAULT ''")
    if "target_city" not in columns:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN target_city TEXT DEFAULT ''")
    if "major" not in columns:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN major TEXT DEFAULT 'General'")
    if "milestone_name" not in columns:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN milestone_name TEXT DEFAULT ''")
    if "milestone_date" not in columns:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN milestone_date TEXT DEFAULT ''")
    if "profile_completed" not in columns:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN profile_completed INTEGER DEFAULT 0")

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
    
    # Schema migration for notepad
    cursor.execute("PRAGMA table_info(notepad)")
    np_cols = [row[1] for row in cursor.fetchall()]
    if "category" not in np_cols:
        cursor.execute("ALTER TABLE notepad ADD COLUMN category TEXT DEFAULT 'General'")
    
    cursor.execute("INSERT OR IGNORE INTO user_profile (id, name, hometown, target_goal, target_university, target_city, major, milestone_name, milestone_date, profile_completed, level, xp, streak) VALUES (1, 'Learner', '', '', '', '', 'General', '', '', 0, 'A1', 0, 0)")
    conn.commit()
    conn.close()

def get_user_profile_data():
    db_path = get_sqlite_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, hometown, target_goal, target_university, target_city, major, milestone_name, milestone_date, profile_completed, level, xp, streak FROM user_profile WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "name": row[0] or "Learner",
            "hometown": row[1] or "",
            "target_goal": row[2] or "",
            "target_university": row[3] or "",
            "target_city": row[4] or "",
            "major": row[5] or "General",
            "milestone_name": row[6] or "",
            "milestone_date": row[7] or "",
            "profile_completed": bool(row[8]),
            "level": row[9] or "A1",
            "xp": row[10] or 0,
            "streak": row[11] or 0
        }
    return {"name": "Learner", "hometown": "", "target_goal": "", "target_university": "", "target_city": "", "major": "General", "milestone_name": "", "milestone_date": "", "profile_completed": False, "level": "A1", "xp": 0, "streak": 0}

def save_user_profile_data(name, hometown, target_goal="", target_university="", target_city="", major="General", milestone_name="", milestone_date="", profile_completed=1):
    db_path = get_sqlite_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE user_profile SET name = ?, hometown = ?, target_goal = ?, target_university = ?, target_city = ?, major = ?, milestone_name = ?, milestone_date = ?, profile_completed = ?, last_active = CURRENT_TIMESTAMP WHERE id = 1",
        (name.strip(), hometown.strip(), target_goal.strip(), target_university.strip(), target_city.strip(), major.strip(), milestone_name.strip(), milestone_date.strip(), 1 if profile_completed else 0)
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
