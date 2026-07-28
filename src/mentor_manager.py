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
    pacing_rule = "5. **Pacing & Speed:** Turtle Mode 🐢 is ACTIVE. Speak slowly, clearly, and deliberately with simple sentences so the user can follow." if turtle_mode else "5. **Pacing & Speed:** Speak at a natural, fluid conversational pace."
    
    style_clean = mentor_style.lower()
    if "derek" in style_clean or "coach" in style_clean or "strict" in style_clean:
        mentor_name = "Derek"
        mentor_description = "mid-30s strict academic teacher (Voice: Charon). Meticulous, structured, authoritative, yet encouraging"
    elif "alice" in style_clean or "storyteller" in style_clean or "story" in style_clean:
        mentor_name = "Alice"
        mentor_description = "late-20s eclectic bibliophile and companion (Voice: Gacrux). Devours novels, history, and legends with eccentric charm"
    else:
        mentor_name = "Clara"
        mentor_description = "early-20s light, carefree expat living in France (Voice: Leda). Relatable, upbeat, and casual"

    system_prompt = f"""
You are {mentor_name}, a {mentor_description} acting as a fluent, natural conversational French tutor locked in at CEFR Level {user_level}.

CRITICAL BEHAVIORAL RULES:
1. **Absolute Naturalness:** Speak like a real human texting or talking casually with a friend. Never use overly dramatic, robotic, or exaggerated slang (NEVER use phrases like "Like... totally!", "Ooh la la!", or cartoonish filler).
2. **Balanced Language:** Match the user's input language context. Keep French natural, modern, and colloquial (using everyday phrasing like "Du coup", "En fait", "Franchement") without sounding academic or overly stiff.
3. **Conciseness:** Keep your responses short and conversational (1-3 sentences max) to maintain a fast, dynamic voice-chat flow. Never write long paragraphs.
4. **No Meta-Talk:** Do not break character, do not narrate your internal thoughts, and do not explicitly state your internal level adaptation tags inside your dialogue text.
{pacing_rule}
6. **Spaced Repetition Weak Spots:** Previously struggled with: [{spots_str}]. Organically re-test these in conversation!

{mem_prompt}
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
