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

def create_chat(client, user_level, mentor_style, weak_spots=None, user_memories=None):
    return client.chats.create(
        model="gemini-3.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=get_system_instruction(user_level, mentor_style, weak_spots, user_memories),
            temperature=0.7,
            response_mime_type="application/json",
            response_schema=TutorResponse
        )
    )

def update_chat_persona(chat, user_level, mentor_style, weak_spots=None, user_memories=None):
    chat.config.system_instruction = get_system_instruction(user_level, mentor_style, weak_spots, user_memories)

RAG_ENABLED = True
IS_HEALING = False

def heal_rag_connection(client):
    global RAG_ENABLED, IS_HEALING
    # Delay first check slightly to let current user turn finish
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
                print("\n[Warning: Embedding server offline. Bypassing RAG and starting background self-healing...]")
                threading.Thread(target=heal_rag_connection, args=(client,), daemon=True).start()
            augmented_message = user_input
        
    max_retries = 3
    delay = 2.0
    for attempt in range(max_retries):
        try:
            response = chat.send_message(augmented_message)
            return response.text
        except APIError as e:
            if attempt == max_retries - 1:
                print(f"\n[Gemini API error after {max_retries} attempts: {e}]")
                break
            
            # 503 Service Unavailable, 429 Rate Limit, or temporary errors are retried
            sleep_time = (delay * (2 ** attempt)) + random.uniform(0.1, 0.5)
            print(f"\n[API busy (Error {e.code}). Retrying in {sleep_time:.1f}s... (Attempt {attempt + 1}/{max_retries})]")
            time.sleep(sleep_time)
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"\n[Error after {max_retries} attempts: {e}]")
                break
            
            sleep_time = (delay * (2 ** attempt)) + random.uniform(0.1, 0.5)
            print(f"\n[Connection issue. Retrying in {sleep_time:.1f}s... (Attempt {attempt + 1}/{max_retries})]")
            time.sleep(sleep_time)

    # Friendly fallback JSON response matching Pydantic schema
    fallback_response = {
        "french_response": "Désolé, je me repose un petit moment. Reprenons notre conversation dans un instant !",
        "mentor_feedback": "The AI mentor is taking a quick breather due to high traffic. Let's try sending that again!",
        "internal_adaptation_level": "None (System rate-limited)",
        "is_exit": False,
        "new_vocabulary_introduced": [],
        "diagnostics": "API_TEMPORARY_LIMIT_BREATHER"
    }
    return json.dumps(fallback_response)
