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
    french_response: str = Field(description="Main dialogue response from the mentor. For Clara, this includes her lively, code-switched French/English dialogue and inline A1 phrase breakdowns.")
    mentor_feedback: Optional[str] = Field(default=None, description="Friendly coaching tips, English survival phrase French equivalents, grammar breakdowns, or accent notes.")
    phonetic_breakdown: Optional[str] = Field(default=None, description="Phonetics, liaisons, or pronunciation guide.")
    internal_adaptation_level: str = Field(description="Current adapted CEFR level tag, e.g. A1, A2, B1.")
    is_exit: bool = Field(default=False)
    new_vocabulary_introduced: list[str] = Field(default_factory=list, description="List of new French terms or slang introduced in this turn.")
    diagnostics: Optional[str] = Field(default=None)

from mentor_manager import build_mentor_instructions

def get_system_instruction(user_level, mentor_style, weak_spots=None, user_memories=None, turtle_mode=False, user_name="Learner", user_hometown="", target_goal="", target_university="", target_city="", major="General", milestone_name="", milestone_date="", days_until_milestone=None):
    return build_mentor_instructions(user_level, mentor_style, user_memories, weak_spots, turtle_mode, user_name, user_hometown, target_goal, target_university, target_city, major, milestone_name, milestone_date, days_until_milestone)

MODEL_NAME = "gemini-flash-latest"  # Efficient, high-limit Gemini Flash model

def create_chat(client, user_level, mentor_style, weak_spots=None, user_memories=None, turtle_mode=False, user_name="Learner", user_hometown="", target_goal="", target_university="", target_city="", major="General", milestone_name="", milestone_date="", days_until_milestone=None):
    models_to_try = ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-2.0-flash"]
    sys_inst = get_system_instruction(user_level, mentor_style, weak_spots, user_memories, turtle_mode, user_name, user_hometown, target_goal, target_university, target_city, major, milestone_name, milestone_date, days_until_milestone)
    
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

def update_chat_persona(client, user_level, mentor_style, weak_spots=None, user_memories=None, turtle_mode=False, user_name="Learner", user_hometown="", target_goal="", target_university="", target_city="", major="General", milestone_name="", milestone_date="", days_until_milestone=None):
    return create_chat(client, user_level, mentor_style, weak_spots, user_memories, turtle_mode, user_name, user_hometown, target_goal, target_university, target_city, major, milestone_name, milestone_date, days_until_milestone)

import re

def extract_retry_seconds(error_message):
    """
    Parses the server's requested retry delay in seconds from 429 error messages.
    Supports formats like 'Please retry in 14.5s', 'retry after 10 seconds', etc.
    """
    if not error_message:
        return None
    msg_str = str(error_message)
    match = re.search(r'retry\s+(?:in|after)\s+(\d+(?:\.\d+)?)\s*s(?:ec(?:onds)?)?', msg_str, re.IGNORECASE)
    if not match:
        match = re.search(r'(\d+(?:\.\d+)?)\s*s(?:ec(?:onds)?)?\s+retry', msg_str, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return None

def retry_with_exponential_backoff(func, max_retries=5, initial_delay=1.0, max_delay=32.0):
    """
    Executes func() with exponential backoff and random jitter.
    Respects server-sent 'Please retry in Xs' requested delays on HTTP 429.
    """
    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except APIError as e:
            code = getattr(e, 'code', None) or '429'
            msg = getattr(e, 'message', str(e))
            print(f"\n[Gemini API Rate Limit Notice (Status Code: {code}) - {msg}]")
            
            if attempt == max_retries:
                print(f"[Max retries ({max_retries}) reached. Switching to graceful breather fallback.]")
                raise e
            
            server_delay = extract_retry_seconds(msg) or extract_retry_seconds(str(e))
            if server_delay is not None and server_delay > 0:
                safety_buffer = 1.0  # Buffer margin to guarantee quota window clearance
                sleep_time = server_delay + safety_buffer
                print(f"⏳ [Server-Requested Quota Wait]: Server asked to wait {server_delay:.1f}s. Sleeping {sleep_time:.1f}s (+1.0s buffer)... (Attempt {attempt}/{max_retries})")
            else:
                jitter = random.uniform(0.2, 0.8)
                sleep_time = min(delay + jitter, max_delay)
                print(f"⏳ [Rate Limit Breather]: Pausing for {sleep_time:.1f}s to clear quota window... (Attempt {attempt}/{max_retries})")
            
            time.sleep(sleep_time)
            delay *= 2.0
        except Exception as e:
            is_timeout = "timeout" in str(e).lower() or "connect" in str(e).lower()
            if is_timeout:
                print("\n🌐 [NETWORK DIAGNOSTIC ADVISORY]: Connection timed out while contacting Google Gemini servers.")
                print("👉 Tip: Please check your active VPN, firewall rules, or internet connection!")
            
            if attempt == max_retries:
                print(f"[Max retries ({max_retries}) reached for {type(e).__name__}.]")
                raise e

            server_delay = extract_retry_seconds(str(e))
            if server_delay is not None and server_delay > 0:
                safety_buffer = 1.0
                sleep_time = server_delay + safety_buffer
                print(f"⏳ [Server-Requested Retry Wait]: Server asked to wait {server_delay:.1f}s. Sleeping {sleep_time:.1f}s (+1.0s buffer)... (Attempt {attempt}/{max_retries})")
            else:
                jitter = random.uniform(0.2, 0.8)
                sleep_time = min(delay + jitter, max_delay)
                print(f"⏳ [Network Retry Breather]: Retrying in {sleep_time:.1f}s... (Attempt {attempt}/{max_retries})")
            
            time.sleep(sleep_time)
            delay *= 2.0

def infer_error_category(rule_text):
    r = str(rule_text).lower()
    if "gender" in r or "genre" in r or "le/la" in r or "un/une" in r or "masculin" in r or "féminin" in r:
        return "Gender Agreement"
    elif "conjugat" in r or "tense" in r or "temps" in r or "verb" in r or "verbe" in r or "imparfait" in r or "passé" in r:
        return "Conjugation & Tenses"
    elif "preposition" in r or "à " in r or "en " in r or "de " in r:
        return "Prepositions"
    elif "vocab" in r or "word" in r or "mot" in r or "sens" in r:
        return "Vocabulary"
    elif "pronounc" in r or "accent" in r or "phonet" in r or "liaison" in r:
        return "Pronunciation"
    return "Syntax & Grammar"

def process_notepad_tags(raw_text, user_input, mentor_name="Mentor"):
    if not raw_text or "[NOTEPAD]" not in raw_text:
        return raw_text
    try:
        start_idx = raw_text.find("[NOTEPAD]")
        end_idx = raw_text.find("[/NOTEPAD]")
        if start_idx != -1 and end_idx != -1:
            tag_content = raw_text[start_idx + 9:end_idx].strip()
            clean_text = (raw_text[:start_idx] + raw_text[end_idx + 11:]).strip()
            
            parts = tag_content.split("|")
            orig, corr, rule, cat = user_input, "", "Grammar Correction", "General"
            for p in parts:
                p_str = p.strip()
                if p_str.startswith("Original:"):
                    orig = p_str[9:].strip()
                elif p_str.startswith("Corrected:"):
                    corr = p_str[10:].strip()
                elif p_str.startswith("Rule:"):
                    rule = p_str[5:].strip()
                elif p_str.startswith("Category:"):
                    cat = p_str[9:].strip()
            
            if cat == "General":
                cat = infer_error_category(rule)

            if corr:
                from database import save_notepad_entry
                save_notepad_entry(mentor_name, orig, corr, rule, cat)
            return clean_text
    except Exception:
        pass
    return raw_text

def clean_json_string(text):
    if not text:
        return ""
    cleaned = str(text).strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()

def parse_json_response(raw_text):
    if not raw_text:
        return {}
    raw_str = str(raw_text).strip()
    cleaned_text = raw_str.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned_text)
    except Exception:
        # Fallback: Extract JSON object using regex if text contains extra chatter
        match = re.search(r'\{.*\}', raw_str, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
    return {"french_response": cleaned_text, "mentor_feedback": None}

def handle_user_message(user_input, client, chat, collection=None, mentor_name="Mentor"):
    # Sliding History Windowing: Strictly truncate history to last 6 messages to stay under TPM limits
    if hasattr(chat, "_history") and len(chat._history) > 6:
        chat._history = chat._history[-6:]
    elif hasattr(chat, "history") and len(chat.history) > 6:
        chat.history = chat.history[-6:]

    augmented_message = user_input

    # Try RAG retrieval if collection is available
    if collection:
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
            augmented_message = user_input
        
    try:
        raw_res = retry_with_exponential_backoff(lambda: chat.send_message(augmented_message).text)
        cleaned_res = clean_json_string(raw_res)
        return process_notepad_tags(cleaned_res, user_input, mentor_name)
    except Exception:
        fallback_response = {
            "french_response": "Désolé, la connexion est un peu lente. Peux-tu me répéter ta phrase ?",
            "mentor_feedback": "Rate limit (429) or network timeout encountered. Your session is active—feel free to re-enter your message!",
            "internal_adaptation_level": "Rate Limit Breather Fallback",
            "is_exit": False,
            "new_vocabulary_introduced": [],
            "diagnostics": "NETWORK_TIMEOUT_RETRY"
        }
        return json.dumps(fallback_response)

