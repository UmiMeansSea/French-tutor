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
    if profile:
        user_level = profile.get("cefr_level", "A2")
        mentor_style = profile.get("mentor_style", "Balanced")
        print(f"Welcome back! Loading your saved profile... (Level: {user_level}, Style: {mentor_style})")
    else:
        user_level = input("To get started, what is your current French level? (A1, A2, B1, B2, C1, or C2): ").strip().upper()
        if user_level not in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            print("Defaulting to A2.")
            user_level = 'A2'
            
        mentor_style = select_style_menu()
            
        save_profile(user_level, mentor_style)
        print("Profile saved successfully!")
        
    chat = create_chat(client, user_level, mentor_style)
    
    # Prompt for Voice Mode
    voice_mode = False
    if VOICE_AVAILABLE:
        voice_enable = input("Would you like to enable Voice Mode? (y/n): ").strip().lower()
        voice_mode = voice_enable == 'y'
    else:
        print("\n[Voice Input (STT) is unavailable because speech_recognition or pyaudio is missing. Defaulting to typing mode.]")
    
    print(f"\nAwesome! Your Chameleon Mentor is ready, locked in at {user_level} ({mentor_style}).")
    print("Try asking it: 'Should I use tu or vous with my boss?' or just say 'Bonjour!'")
    print("Tip: Type '/profile' to change profiles; type '/voice' to toggle Voice Mode.\n")

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
                save_profile(user_level, mentor_style)
                update_chat_persona(chat, user_level, mentor_style)
                print(f"\n[Mentor style updated dynamically to: {mentor_style}]\n")
                continue
                
            session_metrics["total_turns"] += 1
            
            reply = handle_user_message(user_input, client, chat, collection)
            try:
                import json
                parsed = json.loads(reply)
                french_resp = parsed.get('french_response', '')
                print(f"\nTutor: {french_resp}")
                if parsed.get('mentor_feedback'):
                    print(f"Feedback: {parsed['mentor_feedback']}")
                
                # Debug / Internal Tracking Output
                if parsed.get('internal_adaptation_level'):
                    print(f"*(Internal Tracking: {parsed['internal_adaptation_level']})*")
                print()
                
                if voice_mode and french_resp:
                    speak_french(french_resp, speed=get_voice_speed(mentor_style))
                if parsed.get('new_vocabulary_introduced'):
                    session_metrics["vocabulary_learned"].extend(parsed['new_vocabulary_introduced'])
                if parsed.get('diagnostics'):
                    session_metrics["diagnostics_flagged"].append(parsed['diagnostics'])
                
                if parsed.get('is_exit'):
                    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
                    os.makedirs(db_dir, exist_ok=True)
                    summary_path = os.path.join(db_dir, f"session_summary_{int(time.time())}.json")
                    with open(summary_path, 'w', encoding='utf-8') as f:
                        json.dump(session_metrics, f, indent=4)
                    
                    print("\n--- Session Report ---")
                    print(f"Turns: {session_metrics['total_turns']}")
                    vocab = ', '.join(session_metrics['vocabulary_learned']) if session_metrics['vocabulary_learned'] else 'None'
                    print(f"New Vocab: {vocab}")
                    print("Diagnostics:")
                    if not session_metrics['diagnostics_flagged']:
                        print(" - None")
                    else:
                        for d in session_metrics['diagnostics_flagged']:
                            print(f" - {d}")
                    print(f"Report saved to: {summary_path}\n")
                    break
            except Exception:
                print(f"\nTutor: {reply}\n")
                if voice_mode:
                    speak_french(reply, speed=get_voice_speed(mentor_style))
        except Exception as e:
            print(f"\n[An error occurred during runtime:]")
            traceback.print_exc()
            if voice_mode:
                print("\n[Error detected in Voice Mode. Automatically switching to typing mode.]\n")
                voice_mode = False

if __name__ == "__main__":
    main()
