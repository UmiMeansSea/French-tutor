import os
import sys
import time
import json
import traceback
from dotenv import load_dotenv

from database import get_chroma_collection, auto_ingest_knowledge
from tutor_bot import create_chat, handle_user_message, update_chat_persona
from user_profile import load_profile, save_profile
from audio_utils import speak_french, listen_to_mic, VOICE_AVAILABLE, TTS_AVAILABLE
from roleplay import select_roleplay_menu
from gamification import add_xp, check_badges
from stats import render_stat_chart, award_stat_xp, DEFAULT_STATS
from memory_manager import extract_session_memories
from mentor_manager import render_mentor_dossier

from google import genai
from google.genai import types

def select_style_menu():
    print("\n--- Choose Your Chameleon Mentor Persona ---")
    print("1. Clara (The Vibrant Expat Friend) 🌸 — Upbeat, quirky, active listener, boosts Charm & Knowledge")
    print("2. Derek (The Strict Purist Teacher) 🎩 — Formal, meticulous, grammar academic, boosts Wit & Knowledge")
    print("3. Alice (The Eclectic Bibliophile) 📚 — Captivating, literary, history lover, boosts Courage & Knowledge")
    choice = input("Select mentor (1-3) [Default: 1]: ").strip()
    if choice == '2':
        return "Derek"
    elif choice == '3':
        return "Alice"
    return "Clara"

def select_cefr_level():
    print("\n--- Choose Your CEFR Target Level ---")
    print("1. A1 (Beginner)")
    print("2. A2 (Elementary)")
    print("3. B1 (Intermediate)")
    print("4. B2 (Upper Intermediate)")
    print("5. C1 (Advanced)")
    print("6. C2 (Mastery)")
    choice = input("Select level (1-6) [Default: 1]: ").strip()
    levels = {"1": "A1", "2": "A2", "3": "B1", "4": "B2", "5": "C1", "6": "C2"}
    return levels.get(choice, "A1")

def get_voice_speed(mentor_style):
    s = mentor_style.lower()
    if "derek" in s:
        return 900
    elif "alice" in s:
        return 950
    return 1000

def main():
    # Load environment variables
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY environment variable not found in .env.")
        api_key = input("Please enter your Gemini API Key: ").strip()

    # Initialize Gemini client with resilient 60s timeout for network transport layer
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=60000))

    # Initialize ChromaDB and auto-ingest
    collection = get_chroma_collection()
    auto_ingest_knowledge(client, collection)
    
    # Initialize SQLite Database & User Profile
    from database import init_sqlite_db, get_user_profile_data, save_user_profile_data
    init_sqlite_db()
    user_db_profile = get_user_profile_data()

    if not user_db_profile["profile_completed"]:
        print("\n👋 [WELCOME TO YOUR FRENCH AI TUTOR]: Bonjour !")
        u_name = input("What is your name?: ").strip() or "Learner"
        u_town = input("Where are you from / hometown? (optional): ").strip() or ""
        save_user_profile_data(u_name, u_town, profile_completed=1)
        user_db_profile = get_user_profile_data()
        print(f"\n✨ Enchanté, {user_db_profile['name']}! Profile initialized!\n")

    # Initialize Chat Bot
    print("\nBonjour ! I am your empathetic French AI Mentor.")
    
    profile = load_profile()
    weak_spots = profile.get("weak_spots", []) if profile else []
    user_memories = profile.get("user_memories", {}) if profile else {}
    if profile:
        user_level = profile.get("cefr_level", "A2")
        mentor_style = profile.get("mentor_style", "Balanced")
        print(f"Welcome back, {user_db_profile['name']}! Loading saved profile... (Level: {user_level}, Persona: {mentor_style})")
        if weak_spots:
            print(f"Loaded Spaced Repetition Ledger: {len(weak_spots)} weak spot(s) active.")
        if user_memories.get("mastered_vocab"):
            print(f"Loaded Cross-Session Long-Term Memory: {len(user_memories.get('mastered_vocab', []))} fact(s) recalled.")
    else:
        user_level = input("What is your target French level? (A1, A2, B1, B2, C1, or C2) [Default: A2]: ").strip().upper()
        if user_level not in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            user_level = 'A2'
            
        mentor_style = select_style_menu()
            
        save_profile(user_level, mentor_style, weak_spots=weak_spots, user_memories=user_memories)
        print("Profile saved successfully!")
        
    chat = create_chat(
        client, 
        user_level, 
        mentor_style, 
        weak_spots=weak_spots, 
        user_memories=user_memories,
        user_name=user_db_profile["name"],
        user_hometown=user_db_profile["hometown"]
    )
    
    # Prompt for Voice Mode
    voice_mode = False
    if VOICE_AVAILABLE:
        voice_enable = input("Would you like to enable Voice Mode? (y/n): ").strip().lower()
        voice_mode = voice_enable == 'y'
    else:
        print("\n[Voice Input (STT) is unavailable. Defaulting to typing mode.]")
    
    current_speed = get_voice_speed(mentor_style)
    turtle_mode = False
    
    try:
        from rich_ui import render_top_dashboard, render_command_dashboard, render_mentor_dialogue, status_spinner
        render_top_dashboard(user_level, mentor_style, profile or {})
        render_command_dashboard()
    except Exception:
        print(f"\nAwesome! Your Chameleon Mentor is ready, locked in at {user_level} ({mentor_style}).")
        print("Commands: /call (voice mode) | /dossier (mentor notes) | /hangout | /roleplay | /shadow | /story | /profile | /speed\n")
    except Exception:
        print(f"\nAwesome! Your Chameleon Mentor is ready, locked in at {user_level} ({mentor_style}).")
        print(f"Level {user_lvl} Traveler | XP: {xp} | Daily Streak: {milestone_streak} day(s) 🔥")
        if user_badges:
            print(f"Badges: {', '.join(user_badges)}")
        print("Commands: /call (voice mode) | /dossier (mentor notes) | /stats | /hangout | /roleplay | /shadow | /story | /milestones | /badges | /profile | /speed\n")

    session_metrics = {
        "total_turns": 0,
        "vocabulary_learned": [],
        "diagnostics_flagged": []
    }

    # Start Loop
    while True:
        try:
            if voice_mode:
                user_input = listen_to_mic()
                if not user_input.strip():
                    continue
                else:
                    print(f"You (Spoken): {user_input}")
            else:
                user_input = input("You: ")
        except KeyboardInterrupt:
            print("\n\n[Session Interrupted (Ctrl+C) 🛑. Exiting French Tutor... À bientôt ! 👋]\n")
            break
                
        if user_input.strip().lower() in ['quit', 'exit', '/quit', '/exit']:
            break
                
        if user_input.strip().lower() == '/voice':
            if VOICE_AVAILABLE:
                voice_mode = not voice_mode
                print(f"\n[Voice Mode {'enabled' if voice_mode else 'disabled'}]\n")
            else:
                print("\n[Cannot enable Voice Mode: PyAudio or SpeechRecognition libraries are missing.]\n")
            continue

        if user_input.strip().lower() == '/profile':
            mentor_style = select_style_menu()
            save_profile(user_level, mentor_style, 0, weak_spots, 0, 1, [], {}, user_memories)
            chat = update_chat_persona(client, user_level, mentor_style, weak_spots, user_memories, turtle_mode, user_name=user_db_profile["name"], user_hometown=user_db_profile["hometown"])
            current_speed = get_voice_speed(mentor_style) if not turtle_mode else 650
            try:
                from rich_ui import render_top_dashboard
                render_top_dashboard(user_level, mentor_style, profile or {})
            except Exception:
                print(f"\n[Mentor style updated dynamically to: {mentor_style}]\n")
            continue

        if user_input.strip().lower() == '/speed':
            turtle_mode = not turtle_mode
            chat = update_chat_persona(client, user_level, mentor_style, weak_spots, user_memories, turtle_mode, user_name=user_db_profile["name"], user_hometown=user_db_profile["hometown"])
            if turtle_mode:
                print("\n[Pacing Mode: Turtle 🐢 (Deliberate, slow, clear pacing injected into system prompt)]\n")
            else:
                print("\n[Pacing Mode: Normal 🐇 (Natural fluid speed injected into system prompt)]\n")
            continue

        if user_input.strip().lower() in ['/call', '/voice']:
            voice_mode = not voice_mode
            status_str = "ON (Hands-Free Continuous VAD Mic Active 🎤)" if voice_mode else "OFF (Text Mode ⌨️)"
            print(f"\n[Voice Mode Toggled: {status_str}]\n")
            continue

        if user_input.strip().lower() == '/notepad':
            from database import get_notepad_entries
            from rich_ui import render_notepad_dashboard
            notepad_rows = get_notepad_entries()
            render_notepad_dashboard(notepad_rows)
            continue

        if user_input.strip().lower() == '/vault':
            from database import get_vault_words
            from rich_ui import render_vault_dashboard
            vault_rows = get_vault_words()
            render_vault_dashboard(vault_rows)
            continue

        if user_input.strip().lower() == '/hangout':
            m_clean = mentor_style.lower()
            if "derek" in m_clean or "coach" in m_clean:
                print("\n[Launching Derek's Hangout Session: Quiet University Courtyard & Café Terrace ☕]")
                user_input = "Let's sit in the university courtyard and go over advanced grammar nuances with tea."
            elif "alice" in m_clean or "story" in m_clean:
                print("\n[Launching Alice's Hangout Session: Antiquarian Bookstore & Seine River Bridge 🏛️]")
                user_input = "Let's walk near the ancient bookstore by the Seine river and talk about classic literature."
            else:
                print("\n[Launching Clara's Hangout Session: Indie Record Store & Park Bench 🎧]")
                user_input = "Let's hang out on a park bench, listen to some French indie music, and chat casually."

        if user_input.strip().lower() == '/roleplay':
            scenario = select_roleplay_menu()
            user_input = scenario["prompt"]

        if user_input.strip().lower() == '/shadow':
            user_input = "Please give me 1 native French sentence with proper liaisons for me to shadow and repeat back."
            print("\n[Starting Interactive Shadowing Drill...]\n")

        if user_input.strip().lower() == '/story':
            user_input = f"Please read me a short 3-sentence story in French appropriate for my level ({user_level}), and ask me 2 simple questions."
            print("\n[Starting Daily Reading Session...]\n")

        # Speed Adaptation check
        slow_triggers = ["too fast", "slow down", "je ne comprends pas", "plus lentement"]
        if any(t in user_input.lower() for t in slow_triggers):
            current_speed = max(650, current_speed - 200)
            print(f"*(Speed Adapted: Dropped speaking rate to {current_speed} for clarity)*")
            
        # Atmospheric Status Spinner
        try:
            from rich_ui import status_spinner
            with status_spinner(f"☕ Brewing connection & response with {mentor_style}...", mentor_style):
                reply = handle_user_message(user_input, client, chat, collection, mentor_name=mentor_style)
        except Exception:
            reply = handle_user_message(user_input, client, chat, collection, mentor_name=mentor_style)

        try:
            from tutor_bot import parse_json_response, clean_json_string
            
            raw_clean = clean_json_string(reply)
            parsed = {}
            try:
                parsed = json.loads(raw_clean)
            except (json.JSONDecodeError, Exception):
                parsed = parse_json_response(reply)

            if not isinstance(parsed, dict) or not parsed or not parsed.get('french_response'):
                try:
                    from rich_ui import console
                    console.print("[red]Error parsing mentor response.[/red]")
                except Exception:
                    print("\n[Error parsing mentor response.]\n")
                continue

            french_resp = parsed.get('french_response', '')
            mentor_feedback = parsed.get('mentor_feedback')
            phonetics = parsed.get('phonetic_breakdown')
            diag = parsed.get('diagnostics')
            
            # Check for network timeout or API error fallbacks -> Skip XP rewards
            if diag in ["NETWORK_TIMEOUT_RETRY", "API_TEMPORARY_LIMIT_BREATHER"]:
                try:
                    from rich_ui import render_mentor_dialogue
                    render_mentor_dialogue(parsed, mentor_style)
                except Exception:
                    print(f"\nTutor: {french_resp}")
                    if mentor_feedback:
                        print(f"Feedback: {mentor_feedback}\n")
                continue

            # SUCCESS: Log turn metrics
            session_metrics["total_turns"] += 1
            save_profile(user_level, mentor_style, weak_spots=weak_spots, user_memories=user_memories)
            
            # Sync SQLite persistent storage
            try:
                from database import sync_sqlite_profile, save_vault_word
                sync_sqlite_profile(user_level)
                if parsed.get('new_vocabulary_introduced'):
                    for vocab in parsed['new_vocabulary_introduced']:
                        save_vault_word(vocab, translation=french_resp[:40], cefr_level=user_level)
            except Exception:
                pass

            # Render Dialogue with Rich Panels
            try:
                from rich_ui import render_mentor_dialogue
                render_mentor_dialogue(parsed, mentor_style)
            except Exception:
                print(f"\nTutor: {french_resp}")
                if phonetics:
                    print(f"Phonetics & Blending: {phonetics}")
                if mentor_feedback:
                    print(f"Feedback: {mentor_feedback}")
                print()
            
            # CRITICAL: Explicitly and ONLY pass parsed french_resp to TTS
            if voice_mode and french_resp:
                speak_french(french_resp, mentor_style=mentor_style)

            if parsed.get('new_vocabulary_introduced'):
                session_metrics["vocabulary_learned"].extend(parsed['new_vocabulary_introduced'])
                try:
                    from database import save_vault_word
                    for vocab in parsed['new_vocabulary_introduced']:
                        save_vault_word(vocab, translation=french_resp[:40], cefr_level=user_level)
                except Exception:
                    pass
            if diag:
                session_metrics["diagnostics_flagged"].append(diag)
                weak_spots.append(diag)
                save_profile(user_level, mentor_style, weak_spots=weak_spots, user_memories=user_memories)
            
            if parsed.get('is_exit'):
                profile = extract_session_memories(session_metrics, profile or {})
                user_memories = profile.get("user_memories", {})
                save_profile(user_level, mentor_style, weak_spots=weak_spots, user_memories=user_memories)
                
                db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
                os.makedirs(db_dir, exist_ok=True)
                summary_path = os.path.join(db_dir, f"session_summary_{int(time.time())}.json")
                with open(summary_path, 'w', encoding='utf-8') as f:
                    json.dump(session_metrics, f, indent=4)
                
                print("\n╔════════════════════════════════════════════════════════════╗")
                print("║               🎓 POST-SESSION SUMMARY CARD 🎓               ║")
                print("╠════════════════════════════════════════════════════════════╣")
                print(f"║ 🎭 Mentor Persona:       {mentor_style}")
                print(f"║ 💬 Conversational Turns:  {session_metrics['total_turns']}")
                v_str = ', '.join(session_metrics['vocabulary_learned']) if session_metrics['vocabulary_learned'] else 'None'
                if len(v_str) > 35: v_str = v_str[:32] + "..."
                print(f"║ 📚 Vocabulary Learned:    {v_str}")
                w_str = ', '.join(weak_spots) if weak_spots else 'None recorded'
                if len(w_str) > 35: w_str = w_str[:32] + "..."
                print(f"║ 🎯 Recorded Weak Spots:   {w_str}")
                m_cnt = len(user_memories.get('mastered_vocab', []))
                print(f"║ 🧠 Long-Term Memories:    {m_cnt} Fact(s) Retained")
                print("╚════════════════════════════════════════════════════════════╝\n")
                break
        except Exception as e:
            print(f"\n[An error occurred during runtime:]")
            traceback.print_exc()
            if voice_mode:
                print("\n[Error detected in Voice Mode. Automatically switching to typing mode.]\n")
                voice_mode = False

if __name__ == "__main__":
    main()
