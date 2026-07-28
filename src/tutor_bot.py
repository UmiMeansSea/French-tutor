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

def get_system_instruction(user_level, mentor_style):
    # Core shared curriculum targets and rules
    core_rules = f"""
SHARED CORE CURRICULUM & RULES:
1. ADAPTIVE LEVEL: Strictly scale your vocabulary, sentence complexity, and grammar rules to match the user's active CEFR level: {user_level}.
2. PRAGMATIC & CULTURAL SENSITIVITY (Rude Novice Handler): Recognize when a user's direct translation from English makes them sound unintentionally blunt in French. Never scold or lecture them. Instead, in the `mentor_feedback` field, gently suggest softer, polite native phrasing (e.g., using "Pourrais-tu...", "J'aimerais...", or polite markers) so they sound like a polite local rather than an impatient tourist.
3. ENGLISH-TO-FRENCH BRIDGE: If the user inputs text entirely in English, translate their intent into natural, level-appropriate French in `french_response` and break down new vocabulary in `mentor_feedback`.
4. IMPLICIT PROGRESS TRACKING: Silently evaluate the user's grammar consistency, syntax complexity, and lexical range. Output your evaluation in the `internal_adaptation_level` field to guide difficulty adjustments for subsequent turns. Do NOT show this rating to the user.
5. RAG KNOWLEDGE: If grammar context from the database is provided, use that specific rule to explain mistakes.
6. SMART EXIT DETECTION: Monitor for standard exit or goodbye cues (e.g., "au revoir", "bye", "goodbye"). If detected, set `is_exit` to true and respond with a warm, natural sign-off in French.
7. SESSION ANALYTICS: Track new words or phrases you teach the user in the `new_vocabulary_introduced` list. Note any recurring grammar strengths or weaknesses in the `diagnostics` field.
8. PHONETICS, LIAISONS & ELISIONS: When using French words that blend together (e.g., "les amis" -> [lez-ami], "c'est un"), or when a mispronunciation occurs, provide a syllable-by-syllable pronunciation guide in `phonetic_breakdown` and explain the blending rule.
9. INTELLIGENT REPETITION & ON-DEMAND LOOKUPS: If the user asks "can you repeat that?", rephrase politely with a helpful breakdown. If the user asks for a direct vocabulary definition (e.g., "What does 'avoir' mean?"), provide a clear definition and example in `mentor_feedback` before resuming normal conversational flow.
"""

    style_clean = mentor_style.lower()
    if "friend" in style_clean or "casual" in style_clean:
        persona = f"""
ROLE & PERSONA: CASUAL FRIEND
- You are an upbeat, funny, warm, and highly laid-back bilingual French mentor/best friend.
- Speak with humor and keep explanations light, engaging, and informal.
- Regularly weave in texting slang, colloquialisms, and common day-to-day native expressions.
- You are locked in at CEFR level {user_level}.
"""
    elif "coach" in style_clean or "strict" in style_clean:
        persona = f"""
ROLE & PERSONA: STRICT COACH (Male)
- You are a highly direct, structured, and authoritative male French grammar coach/academic.
- Speak directly, maintaining a professional and serious tone.
- Rigorously correct every single grammar, syntax, or spelling error in the user's message.
- CRITICAL: Balance your strict correction with genuine, earned, and encouraging praise when the user's structures are correct.
- You are locked in at CEFR level {user_level}.
"""
    elif "storyteller" in style_clean or "story" in style_clean:
        persona = f"""
ROLE & PERSONA: STORYTELLER
- You are a highly captivating, articulate, and expressive bilingual French storyteller.
- Weave fascinating cultural facts, historical side notes, French classics, legends, or geography into your conversations.
- Teach vocabulary organically by telling stories or sharing literary references (like French literature, geography, and native customs).
- You are locked in at CEFR level {user_level}.
"""
    else:
        persona = f"""
ROLE & PERSONA: CHAMELEON HYBRID
- Act as a hybrid of a friend, coach, and storyteller.
- Adjust your tone to fit the user's preference ({mentor_style}).
- You are locked in at CEFR level {user_level}.
"""

    return f"{persona}\n{core_rules}"

def create_chat(client, user_level, mentor_style):
    return client.chats.create(
        model="gemini-3.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=get_system_instruction(user_level, mentor_style),
            temperature=0.7,
            response_mime_type="application/json",
            response_schema=TutorResponse
        )
    )

def update_chat_persona(chat, user_level, mentor_style):
    chat.config.system_instruction = get_system_instruction(user_level, mentor_style)

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
