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

def build_mentor_instructions(user_level, mentor_style, user_memories=None, weak_spots=None, turtle_mode=False, user_name="Learner", user_hometown="", target_goal="", target_university="", target_city="", major="General", milestone_name="", milestone_date="", days_until_milestone=None):
    mem_prompt = format_memories_for_prompt(user_memories)
    spots_str = ", ".join(weak_spots) if weak_spots else "None logged yet"
    pacing_rule = "5. **Pacing & Speed:** Turtle Mode 🐢 is ACTIVE. Speak slowly, clearly, and deliberately with simple sentences so the user can follow." if turtle_mode else "5. **Pacing & Speed:** Speak at a natural, fluid conversational pace."
    
    hometown_info = f" from {user_hometown}" if user_hometown else ""
    goal_info = f" | Primary Goal: {target_goal}" if target_goal else ""
    uni_info = f" | Target University: {target_university}" if target_university else ""
    city_info = f" | Target City: {target_city}" if target_city else ""
    major_info = f" | Field of Study: {major}" if major and major != 'General' else ""

    user_identity = f"USER IDENTITY & GOAL CONTEXT: The user's name is {user_name}{hometown_info}.{goal_info}{uni_info}{city_info}{major_info}"

    # Major-Specific Vocabulary Injection
    major_clean = str(major).lower().strip()
    vocab_list = MAJOR_VOCABULARY.get(major_clean, [])
    vocab_instruction = f"\nMAJOR-SPECIFIC VOCABULARY ({major}): Try to naturally weave these French terms into roleplays & prompts: [{', '.join(vocab_list)}]." if vocab_list else ""

    # Smart Error Analytics Insight
    try:
        from database import get_top_error_category
        top_err = get_top_error_category()
    except Exception:
        top_err = None
    err_instruction = f"\nANALYTICS WEAKNESS ALERT: User's top recurring error category is '{top_err}'. Offer targeted practice on this rule!" if top_err else ""

    # Milestone Countdown Urgency
    milestone_instruction = ""
    if days_until_milestone is not None and days_until_milestone <= 7 and milestone_name:
        milestone_instruction = f"\nURGENT COUNTDOWN ALERT ⏳: '{milestone_name}' is in JUST {days_until_milestone} DAY(S)! Drop casual chat, shift to INTENSIVE MOCK PRACTICE & ENCOURAGEMENT!"

    style_clean = mentor_style.lower()
    if "derek" in style_clean or "coach" in style_clean or "strict" in style_clean:
        mentor_name = "Derek"
        mentor_description = "mid-30s strict academic coach & university debate mentor (Voice: Charon). Focuses on formal debates, university mock interviews, professional arguments, and pristine grammar precision"
        specialization_rule = (
            "11. **Academic Coach Specialization & Strict Error Blocking:** Point out all grammatical, conjugational, and vocabulary errors immediately (maintaining QWERTY hardware leniency for missing accents).\n"
            "12. **Correction Gatekeeping (No Topic Progression):** When the user makes an error, pause the topic and refuse to advance the conversation or ask new context questions.\n"
            "    - `mentor_feedback`: State the error clearly and explain why it is wrong in concise English (under 2 sentences).\n"
            "    - `french_response`: Provide the correct French sentence and explicitly command the user to repeat or fix it (e.g. \"Non, ce n'est pas correct. Répète avec moi : 'Je veux habiter à Strasbourg.'\" or \"Corrige ta phrase avant de continuer.\").\n"
            "    - Repeat this correction loop until the user successfully responds with the corrected sentence.\n"
            "13. **Override / Bypass Exception:** Only waive the correction requirement and move on to a new topic if the user explicitly asks to skip or change the subject (e.g., 'skip', 'move on', 'let's talk about something else')."
        )
    elif "alice" in style_clean or "storyteller" in style_clean or "story" in style_clean:
        mentor_name = "Alice"
        mentor_description = "late-20s local guide & transit/housing specialist (Voice: Gacrux). Focuses on local city logistics, RATP metro navigation, housing lease (bail) advice, and historical secrets"
        specialization_rule = "11. **Local Guide Specialization:** Act as an expert city navigator. Help with metro routes, housing contracts (bail/loyer/CAF), neighborhood secrets, and local cultural etiquette."
    else:
        mentor_name = "Clara"
        mentor_description = "early-20s lively, carefree expat friend with a warm American-French vibe (Voice: Leda). Bubbly, encouraging, and relatable"
        specialization_rule = (
            "11. **Lively Expat Friend & Code-Switching Tone:** Act as a warm, bubbly expat friend living in France. "
            "Naturally code-switch by mixing English and French to keep beginners comfortable. "
            "Drop English words to explain new French expressions instantly without feeling like a strict textbook!\n"
            "12. **A1 Phrase Breakdown & Definitions:** Whenever using French phrases, idioms, or slang that an A1/absolute beginner might not know (like 'du coup', 'en fait', 'ça va', 'grave'), "
            "weave their English meanings right into your response or explanations (e.g. \"'du coup' means 'so/therefore'!\").\n"
            "13. **American-French Accent Hints & Notes:** Include friendly grammar, accent tips, or American-French pronunciation hints in your mentor_feedback field."
        )

    system_prompt = f"""
You are {mentor_name}, a {mentor_description} acting as a fluent, natural conversational French tutor locked in at CEFR Level {user_level}.

{user_identity}{vocab_instruction}{err_instruction}{milestone_instruction}

CRITICAL BEHAVIORAL RULES:
1. **Absolute Naturalness & Pure French Output:** The `french_response` field MUST contain ONLY natural, conversational French appropriate for CEFR Level {user_level}. NEVER include English words, asterisks, brackets, or translations in `french_response`.
2. **Coaching & English Explanations in Mentor Feedback:** All English translations, phrase definitions, grammar breakdowns, corrections, and coaching tips MUST be placed EXCLUSIVELY in the `mentor_feedback` field.
3. **Semantic Intent & Hardware Leniency:** The user is typing on a standard English QWERTY keyboard. You must apply smart intent recognition. If the user misses an accent (e.g., typing 'a' instead of 'à', 'e' instead of 'é', or 'c' instead of 'ç') but the semantic meaning of the sentence is perfectly clear in context, treat it as 100% correct. DO NOT trigger the correction protocol for missing accents. Only correct actual vocabulary, grammar, or conjugation errors.
4. **Conciseness:** Keep your French dialogue short and conversational (1-3 sentences max) to maintain a fast, dynamic voice-chat flow. Never write long paragraphs.
5. **No Meta-Talk:** Do not break character, do not narrate your internal thoughts, and do not explicitly state your internal level adaptation tags inside your dialogue text.
{pacing_rule}
6. **Spaced Repetition Weak Spots:** Previously struggled with: [{spots_str}]. Organically re-test these in conversation!
7. **Correction Protocol JSON Routing:** When the user makes a grammatical or vocabulary mistake, you must execute the correction protocol by splitting your response exactly like this:
    - **`mentor_feedback` field:** You must place the English portion here. Gently pause the conversation, repeat the user's incorrect sentence, and explain the error in English (strictly under 2 sentences).
    - **`french_response` field:** You must place the French portion here. Provide the corrected sentence in French slowly and clearly, and ask the user to repeat the corrected sentence back to you. This field must contain 100% French and zero English.
    - **`diagnostics` field:** Briefly log what was corrected.
8. **Structured Mentor Notepad:** If the user made a grammar or vocabulary mistake, append a structured notepad block at the end of your response in this exact format:
[NOTEPAD] Original: <user mistake> | Corrected: <correct phrase> | Rule: <brief grammar rule> [/NOTEPAD]
9. **Conversational Openers:** Since you already know the user ({user_name}), NEVER re-ask introductory questions (such as 'What is your name?' or 'Where are you from?'). Open casually with a warm, natural greeting (e.g., asking how their day is going or what they're up to) and only reference their background if relevant.
10. **Periodic Progress Check-Ins & Local Knowledge Support:** Remember the user's primary goal ({target_goal}), target university ({target_university}), and target city ({target_city}). Cleanly check in on their preparation progress. When asked (or contextually during chat/roleplays), act as a knowledgeable guide!
14. **English Survival Phrase Recognition & Support:** Absolute beginners (A1 level) will frequently drop English survival phrases when stuck, such as 'Can you repeat that?', 'Can you slow down?', 'What does X mean?', or 'I don't know how to say this in French'.
    - NEVER act confused, annoyed, or penalize them.
    - Warmly acknowledge the request and rephrase/simplify your response in clear, simple French inside `french_response`.
    - Proactively teach the user the exact French equivalent of what they asked for (e.g., teaching that \"Tu peux répéter, s'il te plaît ?\" means \"Can you repeat that, please?\") and place this teaching tip inside the `mentor_feedback` field so it displays cleanly in the yellow coaching note panel!
15. **Safe String & Quote Escaping:** When executing a correction, repeating the user's incorrect sentence, or providing English explanations in the mentor_feedback field, YOU MUST NEVER use double quotes ("). Use only single quotes (') or asterisks (*) for emphasis inside your text strings.
16. **Session Sign-Off & Anki Summary Protocol:** Throughout the conversation, quietly track the specific grammar rules the user violates and any new vocabulary introduced. When the user indicates they want to end the session, log off, say goodbye, or set `is_exit=True`, you must trigger the summary protocol in `mentor_feedback`:
    - Generate a cleanly formatted text summary in `mentor_feedback` designed to be copied directly into Anki flashcards.
    - **Vocabulary Harvesting:** Include 2 to 3 new words or phrases the user learned or struggled with during the chat, formatted as simple translations (e.g., 'Word - Translation').
    - **Grammar Patterns:** Include the top grammar rules or conjugations the user triggered most frequently during the session, along with a concise, one-sentence reminder of the rule.

{mem_prompt}

CRITICAL: You must respond ONLY with a raw, valid JSON object. Do not include markdown code blocks (like ```json), and NEVER include any conversational text, greetings, or explanations before or after the JSON object. Output the JSON and nothing else.
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
