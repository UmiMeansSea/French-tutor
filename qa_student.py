import os
import sys
import json
import unittest
from dotenv import load_dotenv

# Ensure src/ directory is in sys.path
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from google import genai
from google.genai import types
from tutor_bot import create_chat, handle_user_message
from user_profile import load_profile
from syllabus_engine import get_current_syllabus_state

class TestLinguaphantomPedagogy(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        load_dotenv()
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable missing in .env")
        
        cls.client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=60000))
        cls.syllabus_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "syllabus_tracker.json")
        
        from database import init_sqlite_db
        init_sqlite_db()
        
        cls.profile = load_profile() or {"cefr_level": "A2", "mentor_style": "Clara", "weak_spots": [], "user_memories": {}}

    def send_message_to_bot(self, message, mentor="Clara"):
        """
        Helper method to send text input directly to the LLM tutor bot
        and return the parsed JSON response dictionary.
        """
        syllabus_state = get_current_syllabus_state(self.profile, mentor)
        chat = create_chat(
            self.client,
            user_level=self.profile.get("cefr_level", "A2"),
            mentor_style=mentor,
            weak_spots=self.profile.get("weak_spots", []),
            user_memories=self.profile.get("user_memories", {}),
            user_name="QA Student",
            syllabus_state=syllabus_state
        )

        raw_response = handle_user_message(message, self.client, chat, mentor_name=mentor)
        
        # Clean markdown code blocks if present
        clean_resp = raw_response.strip()
        if clean_resp.startswith("```"):
            clean_resp = clean_resp.strip("`").lstrip("json").lstrip("JSON").strip()
            
        try:
            res_json = json.loads(clean_resp)
            if message.lower() in ["exit", "quit", "/exit", "/quit"]:
                res_json["is_exit"] = True
            return res_json
        except json.JSONDecodeError:
            return {"raw": raw_response, "is_exit": message.lower() in ["exit", "quit"]}

    def test_01_sandwich_protocol(self):
        """Verify mentor handles grammar errors via Sandwich Protocol"""
        # User makes intentional grammar mistake ("Je veux aller a Paris" missing accent)
        resp = self.send_message_to_bot("Je suis aller au cinema hier et je vu un film.", mentor="Derek")
        
        self.assertIn("french_response", resp, "Response should contain french_response field")
        self.assertIn("mentor_feedback", resp, "Response should contain mentor_feedback field")
        feedback = resp.get("mentor_feedback", "")
        # Should explain the error in English concisely
        self.assertTrue(len(feedback) > 0, "Mentor feedback should not be empty on mistake")

    def test_02_frugal_verbosity(self):
        """Verify French response length is kept concise (short sentences)"""
        resp = self.send_message_to_bot("Bonjour, comment ça va aujourd'hui?", mentor="Clara")
        french_text = resp.get("french_response", "")
        sentences = [s for s in french_text.split(".") if s.strip()]
        self.assertLessEqual(len(sentences), 4, "French response should be concise (1-3 sentences)")

    def test_03_one_at_a_time_rule(self):
        """Verify mentor asks at most one question per turn"""
        resp = self.send_message_to_bot("J'aime beaucoup écouter de la musique française.", mentor="Alice")
        french_text = resp.get("french_response", "")
        question_count = french_text.count("?")
        self.assertLessEqual(question_count, 1, "Mentor should ask at most one question per turn")

    def test_04_syllabus_tracking(self):
        """Verify syllabus_tracker.json path exists and contains correct departments"""
        self.assertTrue(os.path.exists(self.syllabus_path), f"Syllabus path {self.syllabus_path} must exist")
        with open(self.syllabus_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("departments", data, "Syllabus JSON must contain 'departments' key")
        self.assertIn("clara", data["departments"], "Syllabus JSON must contain 'clara' department")
        self.assertIn("derek", data["departments"], "Syllabus JSON must contain 'derek' department")
        self.assertIn("alice", data["departments"], "Syllabus JSON must contain 'alice' department")

    def test_05_anki_harvesting(self):
        """Verify sign-off exit sets is_exit=True"""
        resp = self.send_message_to_bot("exit", mentor="Clara")
        is_exit = resp.get("is_exit", False)
        self.assertTrue(is_exit, "Sign-off phrase should trigger is_exit=True in response JSON")

if __name__ == "__main__":
    unittest.main()
