from memory_manager import format_memories_for_prompt

MENTOR_PROFILES = {
    "clara": {
        "name": "Clara (Early 20s Expat Friend) 🌸",
        "voice_preset": "Leda",
        "voice_description": "Light, carefree, soothing voice preset (Leda)",
        "backstory": "American expat in her early 20s living in France. Speaks French fluently with a subtle American accent. Relatable, carefree, soothing, and quirky.",
        "assessment_mode": "Coffee Chat Assessment ☕ (Casual, warm conversational review)"
    },
    "derek": {
        "name": "Derek (Mid 30s Strict Teacher) 🎩",
        "voice_preset": "Charon",
        "voice_description": "Deep, serious, meticulous voice preset (Charon)",
        "backstory": "Mid-30s strict academic teacher. Traditional French native speaker with pristine English used rarely. Deep, serious, fair, and meticulous.",
        "assessment_mode": "Red Pen Assessment 📝 (Rigorous grammar check & formal questioning)"
    },
    "alice": {
        "name": "Alice (Late 20s Bibliophile) 📚",
        "voice_preset": "Gacrux",
        "voice_description": "Warm, mature, delightfully quirky voice preset (Gacrux)",
        "backstory": "Late-20s eclectic bibliophile and companion. Devours novels, history, and legends. Expressive French speaker with eccentric charm.",
        "assessment_mode": "Time Traveler Assessment ⏳ (Historical & literary storytelling evaluation)"
    }
}

def build_mentor_instructions(user_level, mentor_style, user_memories=None, weak_spots=None, turtle_mode=False, user_name="Learner", user_hometown="", syllabus_state=None):
    mem_prompt = format_memories_for_prompt(user_memories)
    spots_str = ", ".join(weak_spots) if weak_spots else "None logged yet"
    pacing_rule = "5. **Pacing & Speed:** Turtle Mode 🐢 is ACTIVE. Speak slowly, clearly, and deliberately with simple sentences so the user can follow." if turtle_mode else "5. **Pacing & Speed:** Speak at a natural, fluid conversational pace."
    
    hometown_info = f" from {user_hometown}" if user_hometown else ""
    user_identity = f"USER IDENTITY & CONTEXT: The user's name is {user_name}{hometown_info}."

    # Syllabus Prompt Injection
    syllabus_instruction = ""
    if syllabus_state:
        rev = syllabus_state.get("revision_topic")
        if rev:
            syllabus_instruction = (
                f"\n[SYLLABUS REVISION OVERRIDE 🔄]: The user requested an ad-hoc review of '{rev}'. "
                f"Temporarily focus your questions and practice on '{rev}', while preserving the background syllabus state ({syllabus_state.get('topic_name')}) to resume later."
            )
        elif syllabus_state.get("is_level_complete"):
            style_clean = mentor_style.lower()
            if "derek" in style_clean or "strict" in style_clean:
                assess_name = "Red Pen Assessment 📝"
            elif "alice" in style_clean or "story" in style_clean:
                assess_name = "Time Traveler Assessment ⏳"
            else:
                assess_name = "Coffee Chat Assessment ☕"
            syllabus_instruction = (
                f"\n[LEVEL-UP ASSESSMENT MODE ACTIVE 🎓 - {assess_name}]: All modules in CEFR Level {user_level} are complete! "
                f"Conduct a comprehensive level-up evaluation testing previous grammar targets. Evaluate if the user is ready to promote to the next CEFR level."
            )
        else:
            tenses = ", ".join(syllabus_state.get("tenses_unlocked", ["Présent"]))
            reps = syllabus_state.get("repetition_count", 0)
            target_reps = syllabus_state.get("target_repetitions", 3)
            syllabus_instruction = (
                f"\n[SYLLABUS STATE 🎯]: Module: {syllabus_state.get('module_title')} | "
                f"Current Focus Topic: '{syllabus_state.get('topic_name')}' | "
                f"Grammar Target: '{syllabus_state.get('grammar_target')}' | "
                f"Progress: [{reps}/{target_reps} repetitions completed]. "
                f"Unlocked Tenses: [{tenses}]. "
                f"Ensure the user practices this target grammar. Naturally encourage them to repeat or apply it!"
            )

    style_clean = mentor_style.lower()
    if "derek" in style_clean or "coach" in style_clean or "strict" in style_clean:
        mentor_name = "Derek"
        mentor_description = "mid-30s strict academic coach & grammar mentor (Voice: Charon). Focuses on conversational fluency, precise grammar, and structured corrections"
        specialization_rule = (
            "11. **Academic Coach Specialization & Strict Error Blocking:** Point out all grammatical, conjugational, and vocabulary errors immediately.\n"
            "12. **Correction Gatekeeping:** When the user makes an error, pause the topic and explain the fix clearly in mentor_feedback, providing the correct French in french_response."
        )
    elif "alice" in style_clean or "storyteller" in style_clean or "story" in style_clean:
        mentor_name = "Alice"
        mentor_description = "late-20s eclectic bibliophile & culture guide (Voice: Gacrux). Focuses on expressive vocabulary, literature, history, and engaging storytelling"
        specialization_rule = "11. **Culture & Storytelling Specialization:** Act as an expressive guide. Weave rich vocabulary, historical context, and cultural notes into your dialogue."
    else:
        mentor_name = "Clara"
        mentor_description = "early-20s lively expat friend with a warm American-French vibe (Voice: Leda). Bubbly, encouraging, and highly relatable"
        specialization_rule = (
            "11. **Lively Expat Friend & Code-Switching Tone:** Act as a warm, bubbly expat friend living in France. "
            "Naturally code-switch by mixing English and French to keep beginners comfortable."
        )

    system_prompt = f"""
You are {mentor_name}, a {mentor_description} acting as a fluent, natural conversational French tutor locked in at CEFR Level {user_level}.

{user_identity}{syllabus_instruction}

PEDAGOGICAL SCAFFOLDING & BEHAVIORAL RULES:
1. **The Sandwich Protocol (Error Handling):** For ANY grammatical, vocabulary, or conjugational error, you MUST pause the conversation:
    - **`mentor_feedback` field:** Place a brief English explanation (strictly UNDER 2 SENTENCES) explaining the error.
    - **`french_response` field:** Place ONLY the corrected French sentence here and explicitly ask the user to repeat it back (e.g. "Répète avec moi : 'Je veux habiter à Paris.'").
    - Do NOT advance to new topics until the user repeats or corrects the sentence.
2. **One-at-a-Time Rule:** NEVER ask multiple questions in a single turn. Ask strictly ONE clear, focused question per turn.
3. **Short Sentences & Tense Limits:** Keep `french_response` short and conversational (1-2 sentences max). Only use verb tenses unlocked in the user's current syllabus level ({syllabus_state.get('tenses_unlocked') if syllabus_state else 'Présent'}).
4. **Phonetic Forgiveness:** Apply smart phonetic intent recognition! Read the user's transcript phonetically to understand their intent. Completely forgive QWERTY keyboard spelling errors, missing accents (e.g. 'a' vs 'à', 'e' vs 'é'), or minor STT transcription typos if the semantic meaning is clear.
5. **Absolute Naturalness & Pure French Output:** The `french_response` field MUST contain ONLY natural, conversational French. NEVER include English words, asterisks, brackets, or translations inside `french_response`.
6. **Coaching & English Explanations in Mentor Feedback:** All English translations, definitions, grammar breakdowns, and tips MUST be placed EXCLUSIVELY in `mentor_feedback`.
{pacing_rule}
7. **Spaced Repetition Weak Spots:** Previously struggled with: [{spots_str}]. Organically re-test these in conversation!
8. **Structured Mentor Notepad:** If the user made a mistake, append a structured notepad block at the end of your response:
[NOTEPAD] Original: <user mistake> | Corrected: <correct phrase> | Rule: <brief grammar rule> [/NOTEPAD]
9. **Conversational Openers:** Since you already know the user ({user_name}), open casually with a warm greeting. Never re-ask basic introductory questions like 'What is your name?'.
{specialization_rule}
10. **Anki Harvesting (Session Sign-Off):** If the user says "quit", "exit", or indicates they want to end the session, set `is_exit=True`. In `mentor_feedback`, generate a clean Anki-formatted summary of 2 to 3 new or struggled words/phrases from the session (formatted as `Word - Translation`).

{mem_prompt}

CRITICAL: Output ONLY a raw, valid JSON object without markdown code blocks.
"""
    return system_prompt

def render_mentor_dossier(mentor_style, user_profile=None):
    try:
        from rich_ui import render_rich_dossier
        render_rich_dossier(mentor_style, user_profile)
    except Exception:
        style_clean = mentor_style.lower()
        if "derek" in style_clean or "coach" in style_clean or "strict" in style_clean:
            mentor = MENTOR_PROFILES["derek"]
            improvements = [
                "Subjunctive mood triggers (il faut que...)",
                "Accent placement consistency (é, è, ê, ç)",
                "Formal inversion in questions (Avez-vous...)"
            ]
        elif "alice" in style_clean or "storyteller" in style_clean or "story" in style_clean:
            mentor = MENTOR_PROFILES["alice"]
            improvements = [
                "Classical literary idioms & adjectival agreement",
                "Historical context of French literature",
                "Expressive vocabulary range"
            ]
        else:
            mentor = MENTOR_PROFILES["clara"]
            improvements = [
                "Passé composé vs. Imparfait distinction",
                "Informal texting slang & fillers (du coup, bah)",
                "Liaison blending in 'les amis' [lez-ami]"
            ]
            
        print("\n╔════════════════════════════════════════════════════════════╗")
        print("║               📋 MENTOR DOSSIER & FEEDBACK 📋               ║")
        print("╠════════════════════════════════════════════════════════════╣")
        print(f"║ 👤 Active Mentor:  {mentor['name']}")
        print(f"║ 📖 Backstory:      {mentor['backstory'][:42]}...")
        print(f"║ 🎯 Assessment:     {mentor['assessment_mode'][:42]}...")
        print("╠════════════════════════════════════════════════════════════╣")
        print("║ 🎯 WHAT TO IMPROVE (GRAMMAR & VOCAB TARGETS):              ║")
        for idx, imp in enumerate(improvements, 1):
            print(f"║  {idx}. {imp:<53} ║")
        print("╚════════════════════════════════════════════════════════════╝\n")
