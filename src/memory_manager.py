def format_memories_for_prompt(user_memories):
    if not user_memories:
        return "USER LONG-TERM MEMORY: No previous session facts logged yet."

    lines = ["USER LONG-TERM MEMORY (CROSS-SESSION RECALL):"]
    if user_memories.get("user_interests"):
        lines.append(f"- User Hobbies/Interests: {', '.join(user_memories['user_interests'])}")
    if user_memories.get("favorite_topics"):
        lines.append(f"- Favorite Topics: {', '.join(user_memories['favorite_topics'])}")
    if user_memories.get("mastered_vocab"):
        lines.append(f"- Mastered Vocabulary: {', '.join(user_memories['mastered_vocab'][-10:])}")
    if user_memories.get("recurring_struggles"):
        lines.append(f"- Recurring Weak Spots: {', '.join(user_memories['recurring_struggles'][-5:])}")
        
    return "\n".join(lines)

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
