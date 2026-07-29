import sqlite3
import os

def run_system_check():
    print("🔍 Running French Tutor Bot System Check...\n")
    
    # 1. Check Python Dependencies
    for pkg in ["rich", "edge_tts"]:
        try:
            __import__(pkg)
            print(f"  [OK] Dependency found: {pkg}")
        except ImportError:
            print(f"  [X] Missing dependency: {pkg}")
            
    # Check Google GenAI SDK import
    try:
        from google import genai
        print("  [OK] Dependency found: google.genai")
    except ImportError:
        print("  [X] Missing dependency: google.genai")
            
    # 2. Check SQLite Database & Schema
    db_path = "tutor_data.db"
    print(f"\n📂 Checking Database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = ["user_profile", "notepad"]
    for table in expected_tables:
        if table in tables:
            print(f"  [OK] Table exists: {table}")
        else:
            print(f"  [!] Missing table: {table} (Will be created on app start)")
            
    conn.close()
    
    # 3. Check API Key Configuration
    api_key_set = bool(os.environ.get("GEMINI_API_KEY"))
    if api_key_set:
        print("\n  [OK] GEMINI_API_KEY environment variable detected.")
    else:
        print("\n  [!] GEMINI_API_KEY environment variable not found in current shell session.")
        
    print("\n✨ System check complete!")

if __name__ == "__main__":
    run_system_check()