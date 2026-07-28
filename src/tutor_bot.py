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

def get_system_instruction(user_level, mentor_style, weak_spots=None, user_memories=None):
    return build_mentor_instructions(user_level, mentor_style, user_memories, weak_spots)

MODEL_NAME = "gemini-2.5-flash"  # Active fast Gemini model

def create_chat(client, user_level, mentor_style, weak_spots=None, user_memories=None):
    try:
        return client.chats.create(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(
                system_instruction=get_system_instruction(user_level, mentor_style, weak_spots, user_memories),
                temperature=0.7,
                response_mime_type="application/json",
                response_schema=TutorResponse
            )
        )
    except Exception as e:
        # Fallback to gemini-1.5-flash if 2.5 is unavailable
        return client.chats.create(
            model="gemini-1.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=get_system_instruction(user_level, mentor_style, weak_spots, user_memories),
                temperature=0.7,
                response_mime_type="application/json",
                response_schema=TutorResponse
            )
        )

def update_chat_persona(client, user_level, mentor_style, weak_spots=None, user_memories=None):
    return create_chat(client, user_level, mentor_style, weak_spots, user_memories)

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
            if attempt == max_retries - 1:
                print(f"\n[Gemini API rate limit or error reached (Code {getattr(e, 'code', '429')}). Attempt {attempt + 1}/{max_retries}]")
                break
            
            # Exponential backoff with jitter
            sleep_time = (initial_delay * (2 ** attempt)) + random.uniform(0.2, 0.8)
            print(f"\n[API busy / rate-limited (Error {getattr(e, 'code', '429')}). Retrying in {sleep_time:.1f}s... (Attempt {attempt + 1}/{max_retries})]")
            time.sleep(sleep_time)
        except Exception as e:
            err_str = str(e)
            if attempt == max_retries - 1:
                print(f"\n[Network connection timeout after {max_retries} attempts: {err_str[:60]}...]")
                break
            
            sleep_time = (initial_delay * (2 ** attempt)) + random.uniform(0.2, 0.8)
            print(f"\n[Network timeout. Retrying in {sleep_time:.1f}s... (Attempt {attempt + 1}/{max_retries})]")
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
