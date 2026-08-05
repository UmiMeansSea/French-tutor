from memory_manager import format_memories_for_prompt

MENTOR_PROFILES = {
    "clara": {
        "name": "Clara (Early 20s Expat Friend) 🌸",
        "voice_preset": "Leda",
        "voice_description": "Light, carefree, soothing voice preset (Leda)",
        "backstory": "American expat in her early 20s living in France. Speaks French fluently with a subtle American accent. Relatable, carefree, soothing, and quirky.",
        "perks": "Boosts Charm & Knowledge. Unlocks Indie Record Store & Park Bench Hangouts."
    },
    "derek": {
        "name": "Derek (Mid 30s Strict Teacher) 🎩",
        "voice_preset": "Charon",
        "voice_description": "Deep, serious, meticulous voice preset (Charon)",
        "backstory": "Mid-30s strict academic teacher. Traditional French native speaker with pristine English used rarely. Deep, serious, fair, and meticulous.",
        "perks": "Boosts Wit & Knowledge. Grants Red Pen Amnesty passes & University Courtyard Hangouts."
    },
    "alice": {
        "name": "Alice (Late 20s Bibliophile) 📚",
        "voice_preset": "Gacrux",
        "voice_description": "Warm, mature, delightfully quirky voice preset (Gacrux)",
        "backstory": "Late-20s eclectic bibliophile and companion. Devours novels, history, and legends. Expressive French speaker with eccentric charm.",
        "perks": "Boosts Courage & Knowledge. Unlocks Secret Archives & Antiquarian Bookstore Hangouts."
    }
}

MAJOR_VOCABULARY = {
    "computer science": ["algorithme", "code source", "base de données", "intelligence artificielle", "développement web", "réseau", "programmeur"],
    "business": ["gestion", "commerce international", "chiffre d'affaires", "marketing digital", "entreprise", "stratégie", "investissement"],
    "engineering": ["ingénierie", "conception mécanique", "système embarqué", "innovation", "robotique", "calcul des structures"],
    "medicine": ["diagnostic", "traitement", "médecine générale", "santé publique", "patient", "ordonnance", "consultation"],
    "law": ["droit constitutionnel", "jurisprudence", "avocat", "tribunal", "code civil", "contrat", "législation"],
    "fine arts": ["histoire de l'art", "sculpture", "peinture", "esthétique", "galerie", "patrimoine culturel", "exposition"],
    "literature": ["roman", "poésie", "analyse littéraire", "auteur", "métaphore", "critique littéraire", "ouvrage"]
}

def build_mentor_instructions(user_level, mentor_style, user_memories=None, weak_spots=None, turtle_mode=False, user_name="Learner", user_hometown=""):
    mem_prompt = format_memories_for_prompt(user_memories)
    spots_str = ", ".join(weak_spots) if weak_spots else "None logged yet"
    pacing_rule = "5. **Pacing & Speed:** Turtle Mode 🐢 is ACTIVE. Speak slowly, clearly, and deliberately with simple sentences so the user can follow." if turtle_mode else "5. **Pacing & Speed:** Speak at a natural, fluid conversational pace."
    
    hometown_info = f" from {user_hometown}" if user_hometown else ""
    user_identity = f"USER IDENTITY & CONTEXT: The user's name is {user_name}{hometown_info}."

    # Smart Error Analytics Insight
    try:
        from database import get_top_error_category
        top_err = get_top_error_category()
    except Exception:
        top_err = None
    err_instruction = f"\nANALYTICS WEAKNESS ALERT: User's top recurring error category is '{top_err}'. Offer targeted practice on this rule!" if top_err else ""

    style_clean = mentor_style.lower()
    if "derek" in style_clean or "coach" in style_clean or "strict" in style_clean:
        mentor_name = "Derek"
        mentor_description = "mid-30s strict academic coach & grammar mentor (Voice: Charon). Focuses on conversational fluency, precise grammar, and structured corrections"
        specialization_rule = (
            "11. **Academic Coach Specialization & Strict Error Blocking:** Point out all grammatical, conjugational, and vocabulary errors immediately (maintaining QWERTY hardware leniency for missing accents).\n"
            "12. **Correction Gatekeeping (No Topic Progression):** When the user makes an error, pause the topic and explain the fix clearly.\n"
            "    - `mentor_feedback`: State the error clearly and explain why it is wrong in concise English (under 2 sentences).\n"
            "    - `french_response`: Provide the correct French sentence and command the user to repeat or fix it (e.g. \"Répète avec moi : 'Je veux habiter à Strasbourg.'\")."
        )
    elif "alice" in style_clean or "storyteller" in style_clean or "story" in style_clean:
        mentor_name = "Alice"
        mentor_description = "late-20s eclectic bibliophile & culture guide (Voice: Gacrux). Focuses on expressive vocabulary, literature, history, and engaging storytelling"
        specialization_rule = "11. **Culture & Storytelling Specialization:** Act as an expressive guide. Weave rich vocabulary, historical context, and interesting cultural notes into your dialogue."
    else:
        mentor_name = "Clara"
        mentor_description = "early-20s lively expat friend with a warm American-French vibe (Voice: Leda). Bubbly, encouraging, and highly relatable"
        specialization_rule = (
            "11. **Lively Expat Friend & Code-Switching Tone:** Act as a warm, bubbly expat friend living in France. "
            "Naturally code-switch by mixing English and French to keep beginners comfortable.\n"
            "12. **A1 Phrase Breakdown & Definitions:** Whenever using French phrases or idioms, weave their English meanings right into your response or explanations."
        )

    system_prompt = f"""
You are {mentor_name}, a {mentor_description} acting as a fluent, natural conversational French tutor locked in at CEFR Level {user_level}.

{user_identity}{err_instruction}

CRITICAL BEHAVIORAL RULES:
1. **Absolute Naturalness & Pure French Output:** The `french_response` field MUST contain ONLY natural, conversational French appropriate for CEFR Level {user_level}. NEVER include English words, asterisks, brackets, or translations in `french_response`.
2. **Coaching & English Explanations in Mentor Feedback:** All English translations, phrase definitions, grammar breakdowns, corrections, and coaching tips MUST be placed EXCLUSIVELY in the `mentor_feedback` field.
3. **Semantic Intent & Hardware Leniency:** The user is typing on a standard English QWERTY keyboard. You must apply smart intent recognition. If the user misses an accent (e.g., typing 'a' instead of 'à') but the semantic meaning of the sentence is clear in context, treat it as correct. Only correct actual vocabulary, grammar, or conjugation errors.
4. **Conciseness:** Keep your French dialogue short and conversational (1-3 sentences max) to maintain a dynamic flow.
5. **No Meta-Talk:** Do not break character, do not narrate your internal thoughts.
{pacing_rule}
6. **Spaced Repetition Weak Spots:** Previously struggled with: [{spots_str}]. Organically re-test these in conversation!
7. **Correction Protocol JSON Routing:** When the user makes a mistake, split your response cleanly:
    - **`mentor_feedback` field:** Place English explanation here (strictly under 2 sentences).
    - **`french_response` field:** Provide the corrected sentence in 100% French and ask the user to repeat.
    - **`diagnostics` field:** Briefly log what was corrected.
8. **Structured Mentor Notepad:** If the user made a mistake, append a structured notepad block at the end of your response:
[NOTEPAD] Original: <user mistake> | Corrected: <correct phrase> | Rule: <brief grammar rule> [/NOTEPAD]
9. **Conversational Openers:** Since you already know the user ({user_name}), open casually with a warm greeting. Never re-ask basic introductory questions like 'What is your name?'.
{specialization_rule}
10. **English Survival Phrase Recognition:** Absolute beginners will drop English survival phrases when stuck (e.g. 'Can you repeat that?'). Warmly acknowledge and assist inside `mentor_feedback`.

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
        print(f"║ 🌟 Synergy Perks:  {mentor['perks'][:42]}...")
        print("╠════════════════════════════════════════════════════════════╣")
        print("║ 🎯 WHAT TO IMPROVE (GRAMMAR & VOCAB TARGETS):              ║")
        for idx, imp in enumerate(improvements, 1):
            print(f"║  {idx}. {imp:<53} ║")
        print("╚════════════════════════════════════════════════════════════╝\n")
