import time
import random
import json
import threading
from pydantic import BaseModel, Field
from typing import Optional
from google import genai
from google.genai import types
from google.genai.errors import APIError

class TutorResponse(BaseModel):
    french_response: str
    mentor_feedback: Optional[str] = None
    phonetic_breakdown: Optional[str] = None
    internal_adaptation_level: str
    is_exit: bool
    new_vocabulary_introduced: list[str]
    diagnostics: Optional[str] = None

from mentor_manager import build_mentor_instructions

def get_system_instruction(user_level, mentor_style, weak_spots=None, user_memories=None, turtle_mode=False):
    return build_mentor_instructions(user_level, mentor_style, user_memories, weak_spots, turtle_mode)

MODEL_NAME = "gemini-flash-latest"  # Verified working production model

def create_chat(client, user_level, mentor_style, weak_spots=None, user_memories=None, turtle_mode=False):
    models_to_try = ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-pro-latest", "gemini-2.0-flash"]
    sys_inst = get_system_instruction(user_level, mentor_style, weak_spots, user_memories, turtle_mode)
    
    for m in models_to_try:
        try:
            return client.chats.create(
                model=m,
                config=types.GenerateContentConfig(
                    system_instruction=sys_inst,
                    temperature=0.7,
                    response_mime_type="application/json",
                    response_schema=TutorResponse
                )
            )
        except Exception:
            continue
            
    # Final attempt fallback
    return client.chats.create(
        model="gemini-flash-latest",
        config=types.GenerateContentConfig(
            system_instruction=sys_inst,
            temperature=0.7,
            response_mime_type="application/json",
            response_schema=TutorResponse
        )
    )

def update_chat_persona(client, user_level, mentor_style, weak_spots=None, user_memories=None, turtle_mode=False):
    return create_chat(client, user_level, mentor_style, weak_spots, user_memories, turtle_mode)

RAG_ENABLED = True
IS_HEALING = False

def heal_rag_connection(client):
    global RAG_ENABLED, IS_HEALING
    time.sleep(10)
    while not RAG_ENABLED:
        try:
            client.models.embed_content(
                model="gemini-embedding-001",
                contents="ping connectivity check"
            )
            RAG_ENABLED = True
            IS_HEALING = False
            print("\n[RAG connection re-established. Dynamic document retrieval re-enabled.]\n")
            break
        except Exception:
            time.sleep(15)

def handle_user_message(user_input, client, chat, collection):
    global RAG_ENABLED, IS_HEALING
    
    # Sliding window memory (Keep last 6 messages)
    if hasattr(chat, "_history") and len(chat._history) > 6:
        chat._history = chat._history[-6:]
    elif hasattr(chat, "history") and len(chat.history) > 6:
        chat.history = chat.history[-6:]

    augmented_message = user_input

    if RAG_ENABLED:
        try:
            embed_response = client.models.embed_content(
                model="gemini-embedding-001", 
                contents=user_input
            )
            user_vector = embed_response.embeddings[0].values

            results = collection.query(
                query_embeddings=[user_vector],
                n_results=2
            )
            
            valid_rules = []
            if results['documents'] and results['distances']:
                for i, distance in enumerate(results['distances'][0]):
                    if distance <= 1.2:
                        valid_rules.append(results['documents'][0][i])
            
            if valid_rules:
                context_str = "\n".join(valid_rules)
                augmented_message = f"""
                Database Context: {context_str}
                
                User Message: {user_input}
                """
        except Exception:
            RAG_ENABLED = False
            if not IS_HEALING:
                IS_HEALING = True
                print("\n[Warning: Dynamic RAG database offline. Bypassing context lookup & healing in background...]")
                threading.Thread(target=heal_rag_connection, args=(client,), daemon=True).start()
            augmented_message = user_input
        
    max_retries = 5
    initial_delay = 1.5
    for attempt in range(max_retries):
        try:
            response = chat.send_message(augmented_message)
            return response.text
        except APIError as e:
            code = getattr(e, 'code', 'Unknown HTTP Status')
            msg = getattr(e, 'message', str(e))
            details = getattr(e, 'details', '')
            print(f"\n[Gemini APIError (Status Code: {code}) - Message: {msg}]")
            if details:
                print(f"[API Details: {details}]")
            
            if attempt == max_retries - 1:
                print(f"[Max retries ({max_retries}) exhausted for APIError Code {code}]")
                break
            
            sleep_time = (initial_delay * (2 ** attempt)) + random.uniform(0.2, 0.8)
            print(f"[Retrying in {sleep_time:.1f}s... (Attempt {attempt + 1}/{max_retries})]")
            time.sleep(sleep_time)
        except Exception as e:
            import traceback
            code_str = getattr(e, 'code', None) or getattr(e, 'status_code', None) or 'N/A'
            print(f"\n[API Exception ({type(e).__name__}) - HTTP Status Code: {code_str}]")
            print(f"[Error Detail: {str(e)}]")
            
            if "ConnectTimeout" in type(e).__name__ or "timeout" in str(e).lower() or "ConnectError" in type(e).__name__:
                print("\n🌐 [NETWORK DIAGNOSTIC ADVISORY]: Connection timed out while contacting Google Gemini servers.")
                print("👉 Tip: Please check your internet connection, active VPN, firewall rules, or proxy configuration!\n")

            print("[Traceback Details]:")
            traceback.print_exc()
            
            if attempt == max_retries - 1:
                print(f"[Max retries ({max_retries}) exhausted after network exception]")
                break
            
            sleep_time = (initial_delay * (2 ** attempt)) + random.uniform(0.2, 0.8)
            print(f"[Retrying in {sleep_time:.1f}s... (Attempt {attempt + 1}/{max_retries})]")
            time.sleep(sleep_time)

    # Clean, non-crashing user-facing fallback response
    fallback_response = {
        "french_response": "Désolé, la connexion est un peu lente. Peux-tu me répéter ta phrase ?",
        "mentor_feedback": "Network connection timed out or hit API rate limits. Your session is active—feel free to type your message again!",
        "internal_adaptation_level": "Network Timeout Fallback",
        "is_exit": False,
        "new_vocabulary_introduced": [],
        "diagnostics": "NETWORK_TIMEOUT_RETRY"
    }
    return json.dumps(fallback_response)
