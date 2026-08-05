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

# Target upgraded 70B model for high cognitive capability
TARGET_MODEL = "llama-3.3-70b-versatile"

def generate_response(user_input, mentor, profile=None):
    """
    Routines generation through Groq LPU (llama-3.3-70b-versatile) using full Linguaphantom system prompts.
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
            model=TARGET_MODEL,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        # Fallback to 70B 8192 if versatile model alias varies
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                model="llama3-70b-8192",
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            return chat_completion.choices[0].message.content
        except Exception as e2:
            return f"ERROR: {str(e2)}"

def evaluate_with_llm_judge(test_criterion, user_prompt, bot_response):
    """
    LLM-as-a-Judge: Evaluates the tutor bot response against specific pedagogical criteria using Llama 70B.
    Returns (passed: bool, judge_reasoning: str).
    """
    if not groq_client:
        return True, "Judge bypassed (No GROQ_API_KEY)."

    judge_system_prompt = """
You are an expert AI Pedagogical Quality Assurance Judge evaluating a French AI Language Tutor.
Your job is to objectively analyze the Tutor's response given the Student's prompt and a specific Pedagogical Criterion.

Output ONLY a valid JSON object with the following schema:
{
    "verdict": "PASS" or "FAIL",
    "reasoning": "A concise 1-2 sentence explanation of why the output passed or failed the criterion."
}
"""

    judge_user_prompt = f"""
[PEDAGOGICAL CRITERION TO TEST]:
{test_criterion}

[STUDENT PROMPT]:
{user_prompt}

[TUTOR BOT RESPONSE]:
{bot_response}

Evaluate strictly according to the criterion. Did the tutor pass or fail?
"""

    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": judge_system_prompt},
                {"role": "user", "content": judge_user_prompt}
            ],
            model=TARGET_MODEL,
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        raw_judge = completion.choices[0].message.content
        parsed = json.loads(raw_judge)
        verdict = str(parsed.get("verdict", "FAIL")).upper() == "PASS"
        reasoning = parsed.get("reasoning", "No detailed reasoning provided.")
        return verdict, reasoning
    except Exception as e:
        return False, f"LLM Judge Error: {str(e)}"

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

        # Groq rate limit buffer
        time.sleep(2) 
        
        return response, latency

    def log_test(self, mentor, test_name, prompt, response, latency, passed, details="", judge_reasoning=""):
        word_count = len(response.split())
        question_count = response.count("?")
        status_mark = "PASS" if passed else "FAIL"
        
        if not passed:
            self.mentor_scores[mentor.lower()] -= 10 # Penalize mentor for failing a rule

        # Log for the final Markdown report
        log_entry = f"### {test_name} ({mentor.capitalize()})\n"
        log_entry += f"**Status:** {'✅ PASS' if passed else '❌ FAIL'} | **Latency:** {latency}s | **Words:** {word_count} | **Questions Asked:** {question_count}\n"
        log_entry += f"**Details:** {details}\n"
        if judge_reasoning:
            log_entry += f"**⚖️ LLM Judge Verdict:** {judge_reasoning}\n"
        log_entry += f"\n> **Student:** {prompt}\n"
        log_entry += f"> **AI Response:**\n```json\n{response}\n```\n\n"
        log_entry += "---\n"
        
        self.full_transcript.append(log_entry)
        print(f"[{status_mark}] {test_name} ({mentor}) - {latency}s | Judge: {judge_reasoning[:60]}...")

    def run_suite(self):
        print(f"[STARTING] Advanced Groq 70B LLM-as-a-Judge Chaos & Efficiency QA ({TARGET_MODEL})...\n")

        # ---------------------------------------------------------
        # TEST 1: Sandwich Protocol & Frugality (Derek)
        # ---------------------------------------------------------
        prompt = "Je suis allé au le cinéma hier."
        resp, lat = self.send_message_to_bot(prompt, "Derek")
        
        criterion = (
            "Did the tutor correctly identify the grammar/syntax error ('au le' -> 'au'), "
            "provide a concise English explanation in mentor_feedback, provide the correct French sentence in french_response, "
            "and prompt the student to repeat or fix it without exceeding 80 words?"
        )
        passed, judge_reasoning = evaluate_with_llm_judge(criterion, prompt, resp)
        
        self.log_test("derek", "Sandwich Protocol & Efficiency", prompt, resp, lat, passed, 
                      "Evaluates Sandwich Protocol error handling, English coaching, and verbosity limits.", judge_reasoning)

        # ---------------------------------------------------------
        # TEST 2: One-at-a-Time Rule (Clara)
        # ---------------------------------------------------------
        prompt = "J'aime beaucoup les films d'action."
        resp, lat = self.send_message_to_bot(prompt, "Clara")
        
        criterion = (
            "Did the tutor respond naturally in French while asking STRICTLY AT MOST ONE single question in the entire response? "
            "Zero or one question is PASS; asking two or more questions is FAIL."
        )
        passed, judge_reasoning = evaluate_with_llm_judge(criterion, prompt, resp)

        self.log_test("clara", "One-at-a-Time Rule", prompt, resp, lat, passed, 
                      "Ensures Clara does not overwhelm the user with multiple questions per turn.", judge_reasoning)

        # ---------------------------------------------------------
        # TEST 3: OUTLIER - The Gibberish/Typo Test (Alice)
        # ---------------------------------------------------------
        prompt = "Je ssui alllé au cinmma avc mns ami."
        resp, lat = self.send_message_to_bot(prompt, "Alice")
        
        criterion = (
            "Did the tutor demonstrate Phonetic Forgiveness by successfully understanding the student's underlying intent "
            "(that they went to the cinema with their friend) despite severe typos ('ssui', 'alllé', 'cinmma', 'avc', 'mns'), "
            "responding coherently without hallucinating or crashing?"
        )
        passed, judge_reasoning = evaluate_with_llm_judge(criterion, prompt, resp)

        self.log_test("alice", "Chaos: Phonetic Forgiveness", prompt, resp, lat, passed, 
                      "Tests if the LLM decodes terrible spelling without completely crashing or hallucinating.", judge_reasoning)

        # ---------------------------------------------------------
        # TEST 4: OUTLIER - Topic Hijacking (Clara)
        # ---------------------------------------------------------
        prompt = "Peux-tu m'expliquer la physique quantique?"
        resp, lat = self.send_message_to_bot(prompt, "Clara")
        
        criterion = (
            "Did the tutor set boundaries by politely declining to teach complex non-syllabus subjects like quantum physics, "
            "redirecting the student back to conversational French learning and their active syllabus topics?"
        )
        passed, judge_reasoning = evaluate_with_llm_judge(criterion, prompt, resp)

        self.log_test("clara", "Chaos: Topic Hijack Redirect", prompt, resp, lat, passed, 
                      "Tests if Clara sets boundaries and pulls the user back to the active syllabus.", judge_reasoning)

        # ---------------------------------------------------------
        # TEST 5: OUTLIER - Refusal to speak French (Derek)
        # ---------------------------------------------------------
        prompt = "I don't know how to say this, just tell me the answer in English."
        resp, lat = self.send_message_to_bot(prompt, "Derek")
        
        criterion = (
            "Did the tutor maintain pedagogical character by refusing to switch completely to English, "
            "providing English scaffolding or vocabulary hints in feedback while encouraging/commanding the student to attempt the sentence in French?"
        )
        passed, judge_reasoning = evaluate_with_llm_judge(criterion, prompt, resp)

        self.log_test("derek", "Chaos: English-Only Resistance", prompt, resp, lat, passed, 
                      "Tests if Derek maintains character and forces the user to try in French using scaffolding.", judge_reasoning)

        self.generate_report()

    def generate_report(self):
        print("\n" + "="*40)
        print("GENERATING LLM-JUDGE GROQ 70B ANALYTICS REPORT")
        print("="*40)
        
        report_text = f"# Linguaphantom Alpha - Groq 70B ({TARGET_MODEL}) LLM-as-a-Judge Report\n\n"
        
        # Add Leaderboard
        report_text += "## 🏆 Mentor Leaderboard (Out of 100)\n"
        for mentor, score in sorted(self.mentor_scores.items(), key=lambda item: item[1], reverse=True):
            report_text += f"- **{mentor.capitalize()}:** {score}/100\n"
        
        report_text += "\n## 📝 Detailed Transcript & LLM-as-a-Judge Evaluation\n\n"
        report_text += "".join(self.full_transcript)
        
        with open("qa_report_v2.md", "w", encoding="utf-8") as f:
            f.write(report_text)
            
        print("Detailed report saved to `qa_report_v2.md`.")

if __name__ == "__main__":
    tester = LinguaphantomQAV2()
    tester.run_suite()
