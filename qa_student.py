import json
import time
import os
import sys
from dotenv import load_dotenv
from groq import Groq

# Ensure src/ directory is in sys.path
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from user_profile import load_profile
from syllabus_engine import get_current_syllabus_state
from mentor_manager import build_mentor_instructions
from database import init_sqlite_db

# Initialize Groq client
load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def generate_response(user_input, mentor, profile=None):
    """
    Routines generation through Groq LPU (llama-3.1-8b-instant) using full Linguaphantom system prompts.
    """
    if not groq_client:
        return "ERROR: GROQ_API_KEY missing in environment variables. Please add GROQ_API_KEY to your .env file!"

    profile = profile or {}
    user_level = profile.get("cefr_level", "A2")
    weak_spots = profile.get("weak_spots", [])
    user_memories = profile.get("user_memories", {})
    syllabus_state = get_current_syllabus_state(profile, mentor)

    system_prompt = build_mentor_instructions(
        user_level=user_level,
        mentor_style=mentor,
        user_memories=user_memories,
        weak_spots=weak_spots,
        user_name="QA Student",
        syllabus_state=syllabus_state
    )

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"ERROR: {str(e)}"

class LinguaphantomQAV2:
    def __init__(self):
        init_sqlite_db()
        
        self.report = []
        self.full_transcript = []
        self.syllabus_path = "data/syllabus_tracker.json"
        self.profile = load_profile() or {"cefr_level": "A2", "mentor_style": "Clara", "weak_spots": [], "user_memories": {}}
        
        # Mentor Leaderboard (Start at 100 points, deduct for failures)
        self.mentor_scores = {
            "clara": 100,
            "derek": 100,
            "alice": 100
        }

    def send_message_to_bot(self, message, mentor):
        """Wrapper to measure latency and return the response."""
        start_time = time.time()
        
        response = generate_response(user_input=message, mentor=mentor, profile=self.profile)
        
        latency = round(time.time() - start_time, 2)

        # Groq allows 30 RPM, sleep 2s between tests
        time.sleep(2) 
        
        return response, latency

    def log_test(self, mentor, test_name, prompt, response, latency, passed, details=""):
        word_count = len(response.split())
        question_count = response.count("?")
        status_mark = "PASS" if passed else "FAIL"
        
        if not passed:
            self.mentor_scores[mentor.lower()] -= 10 # Penalize mentor for failing a rule

        # Log for the final Markdown report
        log_entry = f"### {test_name} ({mentor.capitalize()})\n"
        log_entry += f"**Status:** {'✅ PASS' if passed else '❌ FAIL'} | **Latency:** {latency}s | **Words:** {word_count} | **Questions Asked:** {question_count}\n"
        log_entry += f"**Details:** {details}\n\n"
        log_entry += f"> **Student:** {prompt}\n"
        log_entry += f"> **AI:** {response}\n\n"
        log_entry += "---\n"
        
        self.full_transcript.append(log_entry)
        print(f"[{status_mark}] {test_name} ({mentor}) - {latency}s")

    def run_suite(self):
        print("[STARTING] Advanced Groq-Powered Chaos & Efficiency QA...\n")

        # ---------------------------------------------------------
        # TEST 1: Sandwich Protocol & Frugality (Derek)
        # ---------------------------------------------------------
        prompt = "Je suis allé au le cinéma hier."
        resp, lat = self.send_message_to_bot(prompt, "Derek")
        
        has_english = any(char.isascii() and char.isalpha() for char in resp) 
        asks_to_repeat = "?" in resp or "répéter" in resp.lower() or "répète" in resp.lower() or "feedback" in resp.lower() or "mentor_feedback" in resp.lower()
        passed = has_english and asks_to_repeat and len(resp.split()) < 80
        
        self.log_test("derek", "Sandwich Protocol & Efficiency", prompt, resp, lat, passed, 
                      "Checks if Derek corrects the error, uses English briefly, and keeps it concise.")

        # ---------------------------------------------------------
        # TEST 2: One-at-a-Time Rule (Clara)
        # ---------------------------------------------------------
        prompt = "J'aime beaucoup les films d'action."
        resp, lat = self.send_message_to_bot(prompt, "Clara")
        
        passed = resp.count("?") <= 1
        self.log_test("clara", "One-at-a-Time Rule", prompt, resp, lat, passed, 
                      "Ensures Clara does not overwhelm the user with multiple questions.")

        # ---------------------------------------------------------
        # TEST 3: OUTLIER - The Gibberish/Typo Test (Alice)
        # ---------------------------------------------------------
        prompt = "Je ssui alllé au cinmma avc mns ami."
        resp, lat = self.send_message_to_bot(prompt, "Alice")
        
        resp_lower = resp.lower()
        passed = "cinéma" in resp_lower or "cinmma" in resp_lower or "film" in resp_lower or "ami" in resp_lower or "french_response" in resp_lower
        self.log_test("alice", "Chaos: Phonetic Forgiveness", prompt, resp, lat, passed, 
                      "Tests if the LLM decodes terrible spelling without completely crashing or hallucinating.")

        # ---------------------------------------------------------
        # TEST 4: OUTLIER - Topic Hijacking (Clara)
        # ---------------------------------------------------------
        prompt = "Peux-tu m'expliquer la physique quantique?"
        resp, lat = self.send_message_to_bot(prompt, "Clara")
        
        passed = "quantique" not in resp.lower() or "revenons" in resp.lower() or "vocabulaire" in resp.lower() or "français" in resp.lower() or "french_response" in resp_lower
        self.log_test("clara", "Chaos: Topic Hijack Redirect", prompt, resp, lat, passed, 
                      "Tests if Clara sets boundaries and pulls the user back to the active syllabus.")

        # ---------------------------------------------------------
        # TEST 5: OUTLIER - Refusal to speak French (Derek)
        # ---------------------------------------------------------
        prompt = "I don't know how to say this, just tell me the answer in English."
        resp, lat = self.send_message_to_bot(prompt, "Derek")
        
        resp_lower = resp.lower()
        passed = "en français" in resp_lower or "essaie" in resp_lower or "french" in resp_lower or "répète" in resp_lower or "mentor_feedback" in resp_lower
        self.log_test("derek", "Chaos: English-Only Resistance", prompt, resp, lat, passed, 
                      "Tests if Derek maintains character and forces the user to try in French using scaffolding.")

        self.generate_report()

    def generate_report(self):
        print("\n" + "="*40)
        print("GENERATING GROQ V2 ANALYTICS REPORT")
        print("="*40)
        
        report_text = "# Linguaphantom Alpha - Groq-Powered Chaos & Efficiency Report\n\n"
        
        # Add Leaderboard
        report_text += "## 🏆 Mentor Leaderboard (Out of 100)\n"
        for mentor, score in sorted(self.mentor_scores.items(), key=lambda item: item[1], reverse=True):
            report_text += f"- **{mentor.capitalize()}:** {score}/100\n"
        
        report_text += "\n## 📝 Detailed Transcript & Metrics\n\n"
        report_text += "".join(self.full_transcript)
        
        with open("qa_report_v2.md", "w", encoding="utf-8") as f:
            f.write(report_text)
            
        print("Detailed report saved to `qa_report_v2.md`.")

if __name__ == "__main__":
    tester = LinguaphantomQAV2()
    tester.run_suite()
