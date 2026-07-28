import os
import sys
import time
import json
import traceback
from dotenv import load_dotenv
from google import genai

from database import get_chroma_collection, auto_ingest_knowledge
from tutor_bot import create_chat, handle_user_message, update_chat_persona
from user_profile import load_profile, save_profile
from audio_utils import speak_french, listen_to_mic, VOICE_AVAILABLE, TTS_AVAILABLE

def select_style_menu():
    print("\n--- Select Your Mentor Profile ---")
    print("1. Casual Friend (Warm, funny, informal texting slang)")
    print("2. Strict Coach (Direct male academic, rigorous corrections + encouraging praise)")
    print("3. Storyteller (Captivating narratives, cultural facts & classics)")
    choice = input("Select profile (1-3) [Default: 1]: ").strip()
    if choice == '2':
        return "Strict Coach"
    elif choice == '3':
        return "Storyteller"
    else:
        return "Casual Friend"

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

    client = genai.Client(api_key=api_key, http_options={'timeout': 5.0})

    # Initialize ChromaDB and auto-ingest
    collection = get_chroma_collection()
    auto_ingest_knowledge(client, collection)
    
    # Initialize Chat Bot
    print("\nBonjour ! I am your new empathetic French AI Mentor.")
    
    profile = load_profile()
    weak_spots = profile.get("weak_spots", []) if profile else []
    if profile:
        user_level = profile.get("cefr_level", "A2")
        mentor_style = profile.get("mentor_style", "Balanced")
        print(f"Welcome back! Loading your saved profile... (Level: {user_level}, Style: {mentor_style})")
        if weak_spots:
            print(f"Loaded Spaced Repetition Ledger: {len(weak_spots)} weak spot(s) active.")
    else:
        user_level = input("To get started, what is your current French level? (A1, A2, B1, B2, C1, or C2): ").strip().upper()
        if user_level not in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            print("Defaulting to A2.")
            user_level = 'A2'
            
        mentor_style = select_style_menu()
            
        save_profile(user_level, mentor_style, weak_spots=weak_spots)
        print("Profile saved successfully!")
        
    chat = create_chat(client, user_level, mentor_style, weak_spots=weak_spots)
    
    # Prompt for Voice Mode
    voice_mode = False
    if VOICE_AVAILABLE:
        voice_enable = input("Would you like to enable Voice Mode? (y/n): ").strip().lower()
        voice_mode = voice_enable == 'y'
    else:
        print("\n[Voice Input (STT) is unavailable because speech_recognition or pyaudio is missing. Defaulting to typing mode.]")
    
    milestone_streak = profile.get("milestone_streak", 0) if profile else 0
    current_speed = get_voice_speed(mentor_style)
    turtle_mode = False
    
    print(f"\nAwesome! Your Chameleon Mentor is ready, locked in at {user_level} ({mentor_style}).")
    print(f"Daily Milestone Streak: {milestone_streak} day(s) 🔥")
    print("Try asking it: 'Should I use tu or vous with my boss?' or just say 'Bonjour!'")
    print("Commands: /profile (persona) | /speed (turtle/normal) | /voice (audio) | /shadow (echo) | /story (passage) | /milestones (streak)\n")

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
                    print("[Speech not captured. Automatically switching to typing mode. Type '/voice' to speak again.]\n")
                    voice_mode = False
                    continue
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
                save_profile(user_level, mentor_style, milestone_streak, weak_spots)
                update_chat_persona(chat, user_level, mentor_style, weak_spots)
                current_speed = get_voice_speed(mentor_style) if not turtle_mode else 650
                print(f"\n[Mentor style updated dynamically to: {mentor_style}]\n")
                continue

            if user_input.strip().lower() == '/speed':
                turtle_mode = not turtle_mode
                if turtle_mode:
                    current_speed = 650
                    print("\n[Speed Mode: Turtle 🐢 (Fixed slow pace at 650)]\n")
                else:
                    current_speed = get_voice_speed(mentor_style)
                    print(f"\n[Speed Mode: Normal 🐇 (Profile pace at {current_speed})]\n")
                continue

            if user_input.strip().lower() == '/shadow':
                user_input = "Please give me 1 native French sentence with proper liaisons for me to shadow and repeat back."
                print("\n[Starting Interactive Shadowing Drill...]\n")

            if user_input.strip().lower() == '/story':
                user_input = f"Please read me a short 3-sentence story in French appropriate for my level ({user_level}), and ask me 2 simple questions."
                print("\n[Starting Daily Reading Session...]\n")

            if user_input.strip().lower() == '/milestones':
                print(f"\n--- Daily Micro-Milestones (Streak: {milestone_streak} Days 🔥) ---")
                print("1. [x] Core Lesson / Reading Comprehension")
                print("2. [x] Pronunciation & Blending Drill")
                print("3. [x] Shadowing & Conversation Challenge")
                milestone_streak += 1
                save_profile(user_level, mentor_style, milestone_streak, weak_spots)
                print(f"Awesome job! Milestone completed! Streak updated to {milestone_streak} days!\n")
                continue

            # Speed Adaptation check
            slow_triggers = ["too fast", "slow down", "je ne comprends pas", "plus lentement"]
            if any(t in user_input.lower() for t in slow_triggers):
                current_speed = max(650, current_speed - 200)
                print(f"*(Speed Adapted: Dropped speaking rate to {current_speed} for clarity)*")
                
            session_metrics["total_turns"] += 1
            
            reply = handle_user_message(user_input, client, chat, collection)
            try:
                import json
                parsed = json.loads(reply)
                french_resp = parsed.get('french_response', '')
                print(f"\nTutor: {french_resp}")
                if parsed.get('phonetic_breakdown'):
                    print(f"Phonetics & Blending: {parsed['phonetic_breakdown']}")
                if parsed.get('mentor_feedback'):
                    print(f"Feedback: {parsed['mentor_feedback']}")
                
                # Debug / Internal Tracking Output
                if parsed.get('internal_adaptation_level'):
                    print(f"*(Internal Tracking: {parsed['internal_adaptation_level']})*")
                print()
                
                if voice_mode and french_resp:
                    speak_french(french_resp, speed=current_speed)
                if parsed.get('new_vocabulary_introduced'):
                    session_metrics["vocabulary_learned"].extend(parsed['new_vocabulary_introduced'])
                if parsed.get('diagnostics'):
                    session_metrics["diagnostics_flagged"].append(parsed['diagnostics'])
                    weak_spots.append(parsed['diagnostics'])
                    save_profile(user_level, mentor_style, milestone_streak, weak_spots)
                
                if parsed.get('is_exit'):
                    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
                    os.makedirs(db_dir, exist_ok=True)
                    summary_path = os.path.join(db_dir, f"session_summary_{int(time.time())}.json")
                    with open(summary_path, 'w', encoding='utf-8') as f:
                        json.dump(session_metrics, f, indent=4)
                    
                    print("\n╔════════════════════════════════════════════════════════════╗")
                    print("║               🎓 POST-SESSION SUMMARY CARD 🎓               ║")
                    print("╠════════════════════════════════════════════════════════════╣")
                    print(f"║ 🔥 Current Streak:        {milestone_streak} Day(s)")
                    print(f"║ 💬 Conversational Turns:  {session_metrics['total_turns']}")
                    v_str = ', '.join(session_metrics['vocabulary_learned']) if session_metrics['vocabulary_learned'] else 'None'
                    if len(v_str) > 35: v_str = v_str[:32] + "..."
                    print(f"║ 📚 Vocabulary Learned:    {v_str}")
                    w_str = ', '.join(weak_spots) if weak_spots else 'None recorded'
                    if len(w_str) > 35: w_str = w_str[:32] + "..."
                    print(f"║ 🎯 Recorded Weak Spots:   {w_str}")
                    print(f"║ 💾 Saved Summary Path:    db/session_summary_...json")
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
