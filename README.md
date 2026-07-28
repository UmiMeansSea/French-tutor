# 🇫🇷 French AI Tutor & Cultural Mentor (Work in Progress)

> *“A project by a student, for students who want to learn French with a free, friendly companion while actively mastering the language.”* — **Umi**

---

##  Introduction

Welcome! I’m **Umi**, and I built this project because learning a language shouldn't feel like staring at a rigid, expensive textbook. If you want a casual space to chat about your day, practice your conversational skills, or get corrected gently without feeling judged, this is for you.

Think of this project as your personal, free AI friend who happens to be a bilingual French native. It hangs out with you, listens to your day, subtly tracks your progress behind the scenes, and helps you grow naturally—all while keeping things fun and stress-free.

*Note: This project is a **work in progress**, and I’m constantly tinkering with it to make the experience smoother and smarter!*

---

## How It Works

If you are just here to use the tool or see what it does, here is how the magic happens in everyday language:

1. **Your Profile & Vibe:** When you first start the app, it asks for your current French level (from beginner **A1** to advanced **C2**) and how you want your mentor to act. It saves this info locally so you don't have to set it up every time.
2. **Just Chat Naturally:** You can talk to your mentor in French just like you would with a real friend.
3. **The English Bridge:** Don't know how to say a specific phrase in French? Just type it in English! The mentor instantly translates your thought into natural French and explains the new vocabulary in a side note.
4. **Subtle Corrections (No Boring Tests):** Instead of giving you stressful quizzes, the AI watches your grammar and patterns in the background. If it notices you making the same mistake a few times, it casually drops a helpful memory trick or a polite native alternative in the feedback section.
5. **Cultural Tidbits:** As you chat, your mentor tosses in fun real-life tips, texting slang, and social rules used by actual locals in France.
6. **Smart Exit:** Whenever you're done, just say *“au revoir”* or *“bye”*. The mentor says a warm goodbye, wraps up the session, and saves a summary report of your progress.

---

##  Technical Deep Dive (For Developers & Advanced Users)

If you want to look under the hood and understand how the code architecture is built, here is a detailed breakdown of the internal systems, modules, and data flow:

### Project Directory Structure

```text
french_ai_tutor/
├── data/
│   └── knowledge_docs/         # Drop .txt or .md grammar/vocabulary rules here
├── db/
│   ├── chroma_db/              # Persistent local vector database storage
│   └── user_profile.json       # Auto-saved user settings and history
├── src/
│   ├── __init__.py
│   ├── database.py             # ChromaDB connection, auto-ingestion, & distance thresholding
│   ├── user_profile.py         # Persistent profile & session analytics management
│   ├── tutor_bot.py            # Gemini 3.5 Flash logic, Pydantic schemas, & sliding window memory
│   └── main.py                 # Interactive CLI loop & graceful exit handler
├── requirements.txt            # Project dependencies
└── README.md                   # Project documentation

```

### Core Functional Modules & Mechanics

1. **`user_profile.py` (Persistent State & Analytics):**
* **Persistence Layer:** Manages reading and writing to `db/user_profile.json`, ensuring the user's CEFR level (`A1`-`C2`), preferred mentor persona style, and historical tracking persist across application restarts.
* **Session Analytics Engine:** Tracks live metrics during runtime (total conversational turns, bridge translations provided, pattern diagnostics) and compiles them into a structured `session_summary.json` output upon exit.


2. **`database.py` (Advanced RAG & Automated Ingestion):**
* **Auto-Ingestion Watcher:** Scans the `data/knowledge_docs/` directory upon initialization, parsing any new text or markdown grammar documents, chunking them, and embedding them without duplicating pre-existing records.
* **Vector Search & Distance Thresholding:** Leverages a local **ChromaDB** vector store instance (`db/chroma_db/`) to fetch top-K relevant contextual chunks (`n_results=2`) while discarding results that fail mathematical distance thresholds, effectively mitigating model hallucinations.


3. **`tutor_bot.py` (Gemini 3.5 Flash & Structured Output Engine):**
* **Chamberlain / Chameleon System Instructions:** Dynamically injects the user's profile state and historical patterns into the system prompt. It configures Gemini to balance bilingual explanations (English for clarity, native French markers for immersion).
* **Sliding Window Memory:** Manages context token consumption by maintaining a sliding truncation window of the last 5–6 conversation turns.
* **Pydantic Structured Parsing:** Enforces strict JSON schema validation on the LLM output using Pydantic, ensuring type-safe extraction of:
* `french_response` (`str`): The primary conversational reply in French or bridge translation.
* `mentor_feedback` (`Optional[str]`): Contextual side-notes containing pattern diagnostics, memory mnemonics for chronic errors, pragmatic politeness tips, and cultural tidbits.
* `internal_adaptation_level` (`str`): Implicit metric tracking adjustments to linguistic complexity for subsequent turns.
* `is_exit` (`bool`): Boolean flag tripped when conversational closing cues (`au revoir`, `bye`, etc.) are detected.




4. **`main.py` (The Interactive Execution Loop):**
* Initializes the application components, triggers the proactive startup greeting, routes user inputs through the inference pipeline, prints structured CLI feedback blocks, and catches the `is_exit` signal to safely terminate the runtime loop.



---

## 📦 Setup & Installation

1. **Clone the Repository:**
```bash
cd french_ai_tutor

```


2. **Install Dependencies:**
Make sure you have Python 3.10+ installed, then install the required packages:
```bash
pip install google-genai chromadb pydantic openpyxl weasyprint pypdf

```


3. **Configure API Key:**
Set your Google Gemini API key as an environment variable:
```bash
export GEMINI_API_KEY="your-api-key-here"

```


4. **Run the Application:**
```bash
python src/main.py

```
