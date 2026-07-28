import os
import sys
import time
import json
import traceback
from dotenv import load_dotenv
from google import genai
from google.genai import types

from database import get_chroma_collection, auto_ingest_knowledge
from tutor_bot import create_chat, handle_user_message, update_chat_persona
from user_profile import load_profile, save_profile
from audio_utils import speak_french, listen_to_mic, VOICE_AVAILABLE, TTS_AVAILABLE
from roleplay import select_roleplay_menu
from gamification import add_xp, check_badges
from stats import render_stat_chart, award_stat_xp, DEFAULT_STATS
from memory_manager import extract_session_memories
from mentor_manager import render_mentor_dossier

def select_style_menu():
    print("\n--- Choose Your Chameleon Mentor Persona ---")
    print("1. Clara (The Vibrant Expat Friend) 🌸 — Upbeat, quirky, active listener, boosts Charm & Knowledge")
    print("2. Derek (The Strict Purist Teacher) 🎩 — Formal, meticulous, grammar academic, boosts Wit & Knowledge")
    print("3. Alice (The Eclectic Bibliophile) 📚 — Captivating, literary, history lover, boosts Courage & Knowledge")
    choice = input("Select mentor (1-3) [Default: 1]: ").strip()
    if choice == '2':
        return "Derek (Strict Coach)"
    elif choice == '3':
        return "Alice (Storyteller)"
    else:
        return "Clara (Casual Friend)"

def get_voice_speed(style):
    style_clean = style.lower()
    if "friend" in style_clean or "casual" in style_clean:
        return 1150
    elif "coach" in style_clean or "strict" in style_clean:
        return 850
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
    
    # Initialize Chat Bot
    print("\nBonjour ! I am your new empathetic French AI Mentor.")
    
    profile = load_profile()
    weak_spots = profile.get("weak_spots", []) if profile else []
    user_memories = profile.get("user_memories", {}) if profile else {}
    if profile:
        user_level = profile.get("cefr_level", "A2")
        mentor_style = profile.get("mentor_style", "Balanced")
        print(f"Welcome back! Loading your saved profile... (Level: {user_level}, Style: {mentor_style})")
        if weak_spots:
            print(f"Loaded Spaced Repetition Ledger: {len(weak_spots)} weak spot(s) active.")
        if user_memories.get("mastered_vocab"):
            print(f"Loaded Cross-Session Long-Term Memory: {len(user_memories.get('mastered_vocab', []))} fact(s) recalled.")
    else:
        user_level = input("To get started, what is your current French level? (A1, A2, B1, B2, C1, or C2): ").strip().upper()
        if user_level not in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            print("Defaulting to A2.")
            user_level = 'A2'
            
        mentor_style = select_style_menu()
            
        save_profile(user_level, mentor_style, weak_spots=weak_spots, user_memories=user_memories)
        print("Profile saved successfully!")
        
    chat = create_chat(client, user_level, mentor_style, weak_spots=weak_spots, user_memories=user_memories)
    
    # Prompt for Voice Mode
    voice_mode = False
    if VOICE_AVAILABLE:
        voice_enable = input("Would you like to enable Voice Mode? (y/n): ").strip().lower()
        voice_mode = voice_enable == 'y'
    else:
        print("\n[Voice Input (STT) is unavailable because speech_recognition or pyaudio is missing. Defaulting to typing mode.]")
    
    milestone_streak = profile.get("milestone_streak", 0) if profile else 0
    xp = profile.get("xp", 0) if profile else 0
    user_lvl = profile.get("level", 1) if profile else 1
    user_badges = profile.get("badges", []) if profile else []
    rpg_stats = profile.get("rpg_stats", DEFAULT_STATS.copy()) if profile else DEFAULT_STATS.copy()
    current_speed = get_voice_speed(mentor_style)
    turtle_mode = False
    
    try:
        from rich_ui import render_top_dashboard, render_command_dashboard, render_mentor_dialogue, status_spinner
        render_top_dashboard(user_level, mentor_style, profile or {}, rpg_stats)
        render_command_dashboard()
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
                    user_input = input("You (Mic silent/timed out — press Enter to retry mic, or type message): ")
                    if not user_input.strip():
                        continue
                else:
                    print(f"You (Spoken): {user_input}")
            else:
                user_input = input("You: ")
                
            if user_input.lower() in ['quit', 'exit']:
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
                save_profile(user_level, mentor_style, milestone_streak, weak_spots, profile.get("xp", 0), profile.get("level", 1), profile.get("badges", []), rpg_stats, user_memories)
                chat = update_chat_persona(client, user_level, mentor_style, weak_spots, user_memories)
                current_speed = get_voice_speed(mentor_style) if not turtle_mode else 650
                try:
                    from rich_ui import render_top_dashboard
                    render_top_dashboard(user_level, mentor_style, profile or {}, rpg_stats)
                except Exception:
                    print(f"\n[Mentor style updated dynamically to: {mentor_style}]\n")
                continue

            if user_input.strip().lower() == '/speed':
                turtle_mode = not turtle_mode
                chat = update_chat_persona(client, user_level, mentor_style, weak_spots, user_memories, turtle_mode)
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

            if user_input.strip().lower() == '/dossier':
                render_mentor_dossier(mentor_style, profile)
                continue

            if user_input.strip().lower() == '/stats':
                render_stat_chart(rpg_stats, mentor_style)
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
                session_metrics["roleplay_completed"] = True
                profile = add_xp(profile or {}, 50, f"Hangout Session with {mentor_style}")
                rpg_stats, _ = award_stat_xp(rpg_stats, "Charm", 15, mentor_style)
                save_profile(user_level, mentor_style, milestone_streak, weak_spots, profile.get("xp", 0), profile.get("level", 1), profile.get("badges", []), rpg_stats)

            pending_xp_award = None
            if user_input.strip().lower() == '/roleplay':
                scenario = select_roleplay_menu()
                user_input = scenario["prompt"]
                session_metrics["roleplay_completed"] = True
                pending_xp_award = (50, f"Roleplay: {scenario['title']}", "Courage", 15)

            if user_input.strip().lower() == '/badges':
                print(f"\n--- Player Achievement Showcase ---")
                print(f"Level: {profile.get('level', 1)} | XP: {profile.get('xp', 0)}")
                print(f"Badges Unlocked ({len(profile.get('badges', []))}):")
                if not profile.get('badges'):
                    print(" - None unlocked yet. Complete challenges to earn badges!")
                else:
                    for b in profile.get('badges', []):
                        print(f" 🏆 {b}")
                print()
                continue

            if user_input.strip().lower() == '/shadow':
                user_input = "Please give me 1 native French sentence with proper liaisons for me to shadow and repeat back."
                session_metrics["shadow_completed"] = True
                pending_xp_award = (50, "Shadowing Drill", "Wit", 15)
                print("\n[Starting Interactive Shadowing Drill...]\n")

            if user_input.strip().lower() == '/story':
                user_input = f"Please read me a short 3-sentence story in French appropriate for my level ({user_level}), and ask me 2 simple questions."
                pending_xp_award = (40, "Daily Story Reading", "Knowledge", 15)
                print("\n[Starting Daily Reading Session...]\n")

            if user_input.strip().lower() == '/milestones':
                print(f"\n--- Daily Micro-Milestones (Streak: {milestone_streak} Days 🔥) ---")
                print("1. [x] Core Lesson / Reading Comprehension")
                print("2. [x] Pronunciation & Blending Drill")
                print("3. [x] Shadowing & Conversation Challenge")
                milestone_streak += 1
                profile = add_xp(profile or {}, 100, "Daily Milestone Completed")
                rpg_stats, _ = award_stat_xp(rpg_stats, "Knowledge", 10, mentor_style)
                rpg_stats, _ = award_stat_xp(rpg_stats, "Wit", 10, mentor_style)
                save_profile(user_level, mentor_style, milestone_streak, weak_spots, profile.get("xp", 0), profile.get("level", 1), profile.get("badges", []), rpg_stats)
                print(f"Awesome job! Milestone completed! Streak updated to {milestone_streak} days!\n")
                continue

            # Speed Adaptation check
            slow_triggers = ["too fast", "slow down", "je ne comprends pas", "plus lentement"]
            if any(t in user_input.lower() for t in slow_triggers):
                current_speed = max(650, current_speed - 200)
                print(f"*(Speed Adapted: Dropped speaking rate to {current_speed} for clarity)*")
                
            # Atmospheric Status Spinner
            try:
                from rich_ui import status_spinner
                with status_spinner(f"☕ Brewing connection & response with {mentor_style}...", mentor_style):
                    reply = handle_user_message(user_input, client, chat, collection)
            except Exception:
                reply = handle_user_message(user_input, client, chat, collection)

            try:
                import json
                parsed = json.loads(reply)
                french_resp = parsed.get('french_response', '')
                diag = parsed.get('diagnostics')
                
                # Check for network timeout or API error fallbacks -> Skip XP rewards
                if diag in ["NETWORK_TIMEOUT_RETRY", "API_TEMPORARY_LIMIT_BREATHER"]:
                    print(f"\nTutor: {french_resp}")
                    if parsed.get('mentor_feedback'):
                        print(f"Feedback: {parsed['mentor_feedback']}\n")
                    continue

                # SUCCESS: Award XP only after valid API turn response
                session_metrics["total_turns"] += 1
                profile = add_xp(profile or {}, 15, "Conversation Turn")
                rpg_stats, _ = award_stat_xp(rpg_stats, "Charm", 5, mentor_style)

                if pending_xp_award:
                    xp_amt, xp_reason, stat_name, stat_amt = pending_xp_award
                    profile = add_xp(profile or {}, xp_amt, xp_reason)
                    rpg_stats, _ = award_stat_xp(rpg_stats, stat_name, stat_amt, mentor_style)

                profile, _ = check_badges(profile or {}, session_metrics)
                save_profile(user_level, mentor_style, milestone_streak, weak_spots, profile.get("xp", 0), profile.get("level", 1), profile.get("badges", []), rpg_stats)

                # Render Dialogue with Rich Panels
                try:
                    from rich_ui import render_mentor_dialogue
                    render_mentor_dialogue(parsed, mentor_style)
                except Exception:
                    print(f"\nTutor: {french_resp}")
                    if parsed.get('phonetic_breakdown'):
                        print(f"Phonetics & Blending: {parsed['phonetic_breakdown']}")
                    if parsed.get('mentor_feedback'):
                        print(f"Feedback: {parsed['mentor_feedback']}")
                    print()
                
                if voice_mode and french_resp:
                    speak_french(french_resp, speed=current_speed, mentor_style=mentor_style)
                if parsed.get('new_vocabulary_introduced'):
                    session_metrics["vocabulary_learned"].extend(parsed['new_vocabulary_introduced'])
                if diag:
                    session_metrics["diagnostics_flagged"].append(diag)
                    weak_spots.append(diag)
                    rpg_stats, _ = award_stat_xp(rpg_stats, "Memory", 10, mentor_style)
                    save_profile(user_level, mentor_style, milestone_streak, weak_spots, profile.get("xp", 0), profile.get("level", 1), profile.get("badges", []), rpg_stats)
                
                if parsed.get('is_exit'):
                    profile = extract_session_memories(session_metrics, profile or {})
                    user_memories = profile.get("user_memories", {})
                    save_profile(user_level, mentor_style, milestone_streak, weak_spots, profile.get("xp", 0), profile.get("level", 1), profile.get("badges", []), rpg_stats, user_memories)
                    
                    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
                    os.makedirs(db_dir, exist_ok=True)
                    summary_path = os.path.join(db_dir, f"session_summary_{int(time.time())}.json")
                    with open(summary_path, 'w', encoding='utf-8') as f:
                        json.dump(session_metrics, f, indent=4)
                    
                    print("\n╔════════════════════════════════════════════════════════════╗")
                    print("║               🎓 POST-SESSION SUMMARY CARD 🎓               ║")
                    print("╠════════════════════════════════════════════════════════════╣")
                    print(f"║ 🎭 Mentor Synergy:       {mentor_style}")
                    print(f"║ 👤 Player Level:          Level {profile.get('level', 1)} ({profile.get('xp', 0)} XP)")
                    print(f"║ 🔥 Current Streak:        {milestone_streak} Day(s)")
                    print(f"║ 💬 Conversational Turns:  {session_metrics['total_turns']}")
                    v_str = ', '.join(session_metrics['vocabulary_learned']) if session_metrics['vocabulary_learned'] else 'None'
                    if len(v_str) > 35: v_str = v_str[:32] + "..."
                    print(f"║ 📚 Vocabulary Learned:    {v_str}")
                    w_str = ', '.join(weak_spots) if weak_spots else 'None recorded'
                    if len(w_str) > 35: w_str = w_str[:32] + "..."
                    print(f"║ 🎯 Recorded Weak Spots:   {w_str}")
                    m_cnt = len(user_memories.get('mastered_vocab', []))
                    print(f"║ 🧠 Long-Term Memories:    {m_cnt} Fact(s) Retained")
                    b_str = ', '.join(profile.get("badges", [])) if profile.get("badges") else 'None yet'
                    if len(b_str) > 35: b_str = b_str[:32] + "..."
                    print(f"║ 🏆 Badges Unlocked:       {b_str}")
                    print("╚════════════════════════════════════════════════════════════╝\n")
                    break
            except Exception:
                print(f"\nTutor: {reply}\n")
                if voice_mode:
                    speak_french(reply, speed=current_speed)
        except Exception as e:
            print(f"\n[An error occurred during runtime:]")
            traceback.print_exc()
            if voice_mode:
                print("\n[Error detected in Voice Mode. Automatically switching to typing mode.]\n")
                voice_mode = False

if __name__ == "__main__":
    main()
