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
        # Handle dict or object responses from ollama library
        models_list = models_data.get('models', []) if isinstance(models_data, dict) else getattr(models_data, 'models', [])
        names = []
        for m in models_list:
            if isinstance(m, dict):
                names.append(m.get('name', m.get('model', '')))
            else:
                names.append(getattr(m, 'model', getattr(m, 'name', '')))
        
        valid_names = [n for n in names if n]
        if valid_names:
            return valid_names[0]
    except Exception:
        pass
    return "llama3:latest"

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
                messages=self.messages,
                format="json"
            )
            tutor_reply = response['message']['content']
            self.messages.append({"role": "assistant", "content": tutor_reply})
            return tutor_reply
        except Exception as e:
            try:
                # Fallback without explicit format="json" if model doesn't support structured JSON mode
                response = ollama.chat(
                    model=self.model_name,
                    messages=self.messages
                )
                tutor_reply = response['message']['content']
                self.messages.append({"role": "assistant", "content": tutor_reply})
                return tutor_reply
            except Exception as inner_e:
                fallback_resp = {
                    "french_response": "Désolé, Ollama rencontre un petit problème. Peux-tu me répéter ta phrase ?",
                    "mentor_feedback": f"Ollama local inference error ({type(inner_e).__name__}): {str(inner_e)}. Installed model: {self.model_name}.",
                    "phonetic_breakdown": "N/A",
                    "internal_adaptation_level": "Local Ollama Fallback",
                    "is_exit": False,
                    "new_vocabulary_introduced": [],
                    "diagnostics": "OLLAMA_LOCAL_ERROR"
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

