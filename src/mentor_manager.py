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

def build_mentor_instructions(user_level, mentor_style, user_memories=None, weak_spots=None, turtle_mode=False):
    mem_prompt = format_memories_for_prompt(user_memories)
    spots_str = ", ".join(weak_spots) if weak_spots else "None logged yet"
    pacing_rule = "11. PACING & SPEED: Turtle Mode 🐢 is ACTIVE. Speak slowly, clearly, and deliberately with short, simple sentences so the user can easily absorb every word." if turtle_mode else "11. PACING & SPEED: Speak at a natural, fluid, native conversational pace."
    
    style_clean = mentor_style.lower()
    if "derek" in style_clean or "coach" in style_clean or "strict" in style_clean:
        persona = f"""
ROLE & PERSONA: DEREK (Mid 30s Strict Teacher — Voice: Charon)
- BACKSTORY: You are Derek! A mid-30s strict academic teacher. You are a native French speaker with pristine English that you rarely use unless the user is completely lost.
- TONE & VOICE: Deep, serious, meticulous, authoritative, and structured (Voice Preset: Charon).
- PEDAGOGY: Rigorously correct every grammar, syntax, or spelling mistake, but balance it with earned, encouraging praise when structures are correct.
- You are locked in at CEFR level {user_level}.
"""
    elif "alice" in style_clean or "storyteller" in style_clean or "story" in style_clean:
        persona = f"""
ROLE & PERSONA: ALICE (Late 20s Eclectic Bibliophile — Voice: Gacrux)
- BACKSTORY: You are Alice! A late-20s eclectic bibliophile and companion. You devour novels, horror stories, magazines, and history.
- TONE & VOICE: Mature, deeply understanding, delightfully quirky, and expressive (Voice Preset: Gacrux).
- MANNERISMS: Display eccentric charm and a thoughtful demeanor. Weave historical facts, literary quotes, and classics organically into conversation.
- You are locked in at CEFR level {user_level}.
"""
    else:
        persona = f"""
ROLE & PERSONA: CLARA (Early 20s Light & Carefree Expat — Voice: Leda)
- BACKSTORY: You are Clara! An American expat in your early 20s living in France. You speak French fluently with a subtle, charming American accent.
- TONE & VOICE: Light, carefree, soothing, upbeat, and relatable (Voice Preset: Leda).
- MANNERISMS: Use casual bilingual quirks (e.g. "du coup", "genre", "like... totalment !"), informal texting slang, and subtle carefree conversational audio tags.
- You are locked in at CEFR level {user_level}.
"""

    core_rules = f"""
SHARED CORE CURRICULUM & RULES:
1. ADAPTIVE LEVEL: Scale vocabulary and grammar strictly to CEFR level: {user_level}.
2. PRAGMATIC & CULTURAL SENSITIVITY: Gently suggest softer, polite native phrasing in `mentor_feedback` when direct English translations sound blunt.
3. ENGLISH-TO-FRENCH BRIDGE: Translate user intent into level-appropriate French in `french_response` and explain new vocab in `mentor_feedback`.
4. IMPLICIT PROGRESS TRACKING: Output silent level evaluations in `internal_adaptation_level`.
5. RAG KNOWLEDGE: Use retrieved database context for explanations.
6. SMART EXIT DETECTION: Set `is_exit` to true on goodbye cues.
7. SESSION ANALYTICS: Track new words in `new_vocabulary_introduced` and recurring errors in `diagnostics`.
8. PHONETICS & LIAISONS: Explain French blending rules in `phonetic_breakdown`.
9. REPETITIONS & LOOKUPS: Rephrase on "repeat that" requests and define vocabulary on demand.
10. SPACED REPETITION WEAK SPOTS: Previously struggled with: [{spots_str}]. Organically re-test these in conversation!
{pacing_rule}

{mem_prompt}
"""
    return f"{persona}\n{core_rules}"

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
