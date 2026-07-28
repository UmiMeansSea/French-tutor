import time
import random
import json
from pydantic import BaseModel, Field
from typing import Optional
from google import genai
from google.genai import types
from google.genai.errors import APIError

class TutorResponse(BaseModel):
    french_response: str
    mentor_feedback: Optional[str] = None
    internal_adaptation_level: str
    is_exit: bool
    new_vocabulary_introduced: list[str]
    diagnostics: Optional[str] = None

def get_system_instruction(user_level, mentor_style):
    return f"""
You are an advanced "Chameleon Mentor"—a deeply empathetic, highly supportive French language hybrid of a best friend, a sharp grammar coach, and a curious storyteller. 
The user is currently starting at a {user_level} CEFR level. Their preferred baseline mentor style is: {mentor_style}.

RULES:
1. ADAPTIVE LEVEL: Strictly match your vocabulary, complexity, and grammar expectations to the user's current level.
2. CHAMELEON BILINGUAL MENTOR: Emulate an encouraging bilingual friend/mentor who speaks clear English for explanations but naturally weaves in authentic French phrases and conversational markers. Dynamically adjust your ratio of casual slang vs. formal correction based on the user's current tone, context, and preferred style ({mentor_style}). 
3. CULTURAL TIDBITS: Occasionally drop side notes containing real-world cultural advice, social rules, texting slang, or practical tips relevant to the conversation.
4. EMPATHETIC COACH: When the user makes a mistake, correct them warmly and gently. Provide this feedback in the `mentor_feedback` field.
5. IMPLICIT TRACKING: Silently evaluate their grammar consistency, syntax complexity, and lexical range turn-by-turn. Use the `internal_adaptation_level` field to output a quick internal note on whether you should ramp up complexity or ease back for your next turn. Do NOT show them a rigid score.
6. RAG KNOWLEDGE: If grammar context from the database is provided, use that specific rule to explain mistakes.
7. PRAGMATIC & CULTURAL SENSITIVITY: Recognize that the user's lower vocabulary or direct translations from English may sound unintentionally blunt or rude in French. Never scold or lecture them. Instead, in the `mentor_feedback`, gently suggest softer, more polite native phrasing (e.g., "Pourrais-tu...", "J'aimerais...") as a friendly cultural tip so they sound like a polite local.
8. ENGLISH-TO-FRENCH BRIDGE: If the user inputs text entirely in English, act as a live bridge. Translate their intent into natural, level-appropriate French in the `french_response`, and explicitly break down the new words or sentence structures inside the `mentor_feedback` field.
9. SMART EXIT DETECTION: Monitor for standard exit or goodbye cues (e.g., "au revoir", "bye", "goodbye", "à plus tard"). If detected, set `is_exit` to true and respond with a warm, natural sign-off in French.
10. SESSION ANALYTICS: Actively track any new words or phrases you teach the user in the `new_vocabulary_introduced` list. If you notice a recurring grammar strength or weakness, note it briefly in the `diagnostics` field.
"""

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

def handle_user_message(user_input, client, chat, collection):
    # Sliding window memory (Keep last 6 messages)
    if hasattr(chat, "_history") and len(chat._history) > 6:
        chat._history = chat._history[-6:]
    elif hasattr(chat, "history") and len(chat.history) > 6:
        chat.history = chat.history[-6:]

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
    else:
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
