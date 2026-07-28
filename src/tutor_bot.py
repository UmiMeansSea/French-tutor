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

DEFAULT_OLLAMA_MODEL = "gemma2"

class OllamaChatSession:
    def __init__(self, system_instruction, model_name=DEFAULT_OLLAMA_MODEL):
        self.model_name = model_name
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
                    "mentor_feedback": f"Ollama local inference error: {str(inner_e)}. Ensure Ollama server is running locally ('ollama run gemma2')!",
                    "phonetic_breakdown": "N/A",
                    "internal_adaptation_level": "Local Ollama Fallback",
                    "is_exit": False,
                    "new_vocabulary_introduced": [],
                    "diagnostics": "OLLAMA_LOCAL_ERROR"
                }
                return json.dumps(fallback_resp)

def create_chat(client, user_level, mentor_style, weak_spots=None, user_memories=None, turtle_mode=False):
    sys_inst = get_system_instruction(user_level, mentor_style, weak_spots, user_memories, turtle_mode)
    models_to_try = [DEFAULT_OLLAMA_MODEL, "llama3", "qwen2.5", "mistral", "llama2"]
    
    for m in models_to_try:
        try:
            return OllamaChatSession(sys_inst, model_name=m)
        except Exception:
            continue
            
    return OllamaChatSession(sys_inst, model_name=DEFAULT_OLLAMA_MODEL)

def update_chat_persona(client, user_level, mentor_style, weak_spots=None, user_memories=None, turtle_mode=False):
    return create_chat(client, user_level, mentor_style, weak_spots, user_memories, turtle_mode)

def handle_user_message(user_input, client, chat, collection=None):
    if hasattr(chat, "send_message"):
        return chat.send_message(user_input)
    else:
        # Direct Ollama call fallback
        sys_inst = get_system_instruction("A1", "Clara")
        messages = [
            {"role": "system", "content": sys_inst},
            {"role": "user", "content": user_input}
        ]
        response = ollama.chat(model=DEFAULT_OLLAMA_MODEL, messages=messages)
        return response['message']['content']

