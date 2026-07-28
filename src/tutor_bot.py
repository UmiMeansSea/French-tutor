import time
import random
import json
import threading
import ollama
from pydantic import BaseModel, Field
from typing import Optional

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

def get_active_ollama_model():
    try:
        models_data = ollama.list()
        models_list = models_data.get('models', []) if isinstance(models_data, dict) else getattr(models_data, 'models', [])
        names = []
        for m in models_list:
            if isinstance(m, dict):
                names.append(m.get('name', m.get('model', '')))
            else:
                names.append(getattr(m, 'model', getattr(m, 'name', '')))
        
        valid_names = [n for n in names if n]
        # Support Qwen 7B/3B variants and Llama 3
        for pref in ["qwen2.5:7b", "qwen2.5:3b", "qwen2.5", "qwen", "llama3:latest", "llama3"]:
            for name in valid_names:
                if pref in name.lower():
                    return name
        if valid_names:
            return valid_names[0]
    except Exception:
        pass
    return "llama3:latest"

def normalize_tutor_response(tutor_reply):
    if not tutor_reply or not str(tutor_reply).strip() or str(tutor_reply).strip() == "{}":
        tutor_reply = "Coucou ! Enchantée ! Comment ça va aujourd'hui ?"
    
    clean_text = str(tutor_reply).strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    if clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()

    if clean_text == "{}":
        clean_text = "Coucou ! Enchantée ! Comment ça va aujourd'hui ?"

    try:
        data = json.loads(clean_text)
        if isinstance(data, dict) and data:
            fr_text = data.get("french_response") or data.get("response") or data.get("french") or data.get("content")
            if not fr_text or not str(fr_text).strip() or str(fr_text).strip() == "{}":
                fr_text = clean_text
            data["french_response"] = fr_text
            if not data.get("internal_adaptation_level"):
                data["internal_adaptation_level"] = "A1"
            if "is_exit" not in data:
                data["is_exit"] = False
            if "new_vocabulary_introduced" not in data:
                data["new_vocabulary_introduced"] = []
            return json.dumps(data)
    except Exception:
        pass

    # Standard plain text response from local Ollama model
    structured = {
        "french_response": clean_text,
        "mentor_feedback": None,
        "phonetic_breakdown": None,
        "internal_adaptation_level": "A1",
        "is_exit": False,
        "new_vocabulary_introduced": [],
        "diagnostics": None
    }
    return json.dumps(structured)

class OllamaChatSession:
    def __init__(self, system_instruction, model_name=None):
        self.model_name = model_name or get_active_ollama_model()
        self.system_instruction = system_instruction
        self.messages = [
            {"role": "system", "content": system_instruction}
        ]

    def send_message(self, user_content):
        self.messages.append({"role": "user", "content": user_content})
        
        # Sliding window memory (Keep system instruction + last 10 turns)
        if len(self.messages) > 11:
            self.messages = [self.messages[0]] + self.messages[-10:]

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=self.messages
            )
            tutor_reply = response['message']['content']
            norm_reply = normalize_tutor_response(tutor_reply)
            self.messages.append({"role": "assistant", "content": norm_reply})
            return norm_reply
        except Exception as e:
            # Memory error / 500 fallback: try llama3:latest
            if "out-of-memory" in str(e).lower() or "memory" in str(e).lower() or "500" in str(e):
                try:
                    self.model_name = "llama3:latest"
                    response = ollama.chat(
                        model="llama3:latest",
                        messages=self.messages
                    )
                    tutor_reply = response['message']['content']
                    norm_reply = normalize_tutor_response(tutor_reply)
                    self.messages.append({"role": "assistant", "content": norm_reply})
                    return norm_reply
                except Exception:
                    pass

            fallback_resp = {
                "french_response": "Coucou ! Désolé, la mémoire locale est un peu saturée. Peux-tu me répéter ta phrase ?",
                "mentor_feedback": f"Ollama RAM limit reached on {self.model_name}. Switched to lightweight llama3:latest.",
                "phonetic_breakdown": None,
                "internal_adaptation_level": "Local Memory Fallback",
                "is_exit": False,
                "new_vocabulary_introduced": [],
                "diagnostics": "OLLAMA_MEMORY_FALLBACK"
            }
            return json.dumps(fallback_resp)

def create_chat(client, user_level, mentor_style, weak_spots=None, user_memories=None, turtle_mode=False):
    sys_inst = get_system_instruction(user_level, mentor_style, weak_spots, user_memories, turtle_mode)
    active_model = get_active_ollama_model()
    return OllamaChatSession(sys_inst, model_name=active_model)

def update_chat_persona(client, user_level, mentor_style, weak_spots=None, user_memories=None, turtle_mode=False):
    return create_chat(client, user_level, mentor_style, weak_spots, user_memories, turtle_mode)

def handle_user_message(user_input, client, chat, collection=None):
    if hasattr(chat, "send_message"):
        return chat.send_message(user_input)
    else:
        active_model = get_active_ollama_model()
        sys_inst = get_system_instruction("A1", "Clara")
        messages = [
            {"role": "system", "content": sys_inst},
            {"role": "user", "content": user_input}
        ]
        response = ollama.chat(model=active_model, messages=messages)
        return response['message']['content']

