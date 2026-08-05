def format_memories_for_prompt(user_memories):
    from database import get_session_summary
    session_summary = get_session_summary()
    
    lines = ["USER LONG-TERM MEMORY (CROSS-SESSION RECALL):"]
    if session_summary:
        lines.append(f"- Active Session Condensed Summary: {session_summary}")
    if user_memories:
        if user_memories.get("user_interests"):
            lines.append(f"- User Hobbies/Interests: {', '.join(user_memories['user_interests'])}")
        if user_memories.get("favorite_topics"):
            lines.append(f"- Favorite Topics: {', '.join(user_memories['favorite_topics'])}")
        if user_memories.get("mastered_vocab"):
            lines.append(f"- Mastered Vocabulary: {', '.join(user_memories['mastered_vocab'][-10:])}")
        if user_memories.get("recurring_struggles"):
            lines.append(f"- Recurring Weak Spots: {', '.join(user_memories['recurring_struggles'][-5:])}")
        
    return "\n".join(lines)

def summarize_old_turns_async(client, chat, old_turns):
    import threading
    def _run_summary():
        try:
            turns_text = "\n".join([f"{msg.role}: {msg.parts[0].text if hasattr(msg, 'parts') else str(msg)}" for msg in old_turns])
            prompt = f"Summarize the following French tutoring conversation turns into a dense, 2-sentence contextual summary:\n\n{turns_text}"
            res = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            summary_text = res.text.strip() if hasattr(res, 'text') else ""
            if summary_text:
                from database import save_session_summary
                save_session_summary(summary_text)
        except Exception:
            pass
            
    t = threading.Thread(target=_run_summary, daemon=True)
    t.start()

def extract_session_memories(session_metrics, user_profile):
    if not user_profile:
        user_profile = {}
        
    memories = user_profile.get("user_memories", {
        "user_interests": ["French indie music", "Café culture"],
        "favorite_topics": ["Travel", "Gastronomy"],
        "mastered_vocab": [],
        "recurring_struggles": []
    })
    
    # Process vocabulary learned in this session
    new_vocab = session_metrics.get("vocabulary_learned", [])
    for v in new_vocab:
        if v and v not in memories["mastered_vocab"]:
            memories["mastered_vocab"].append(v)
            
    # Process diagnostics
    diag = session_metrics.get("diagnostics_flagged", [])
    for d in diag:
        if d and d not in memories["recurring_struggles"]:
            memories["recurring_struggles"].append(d)
            
    user_profile["user_memories"] = memories
    return user_profile
