import os
import json

SYLLABUS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "syllabus_tracker.json")

def load_syllabus_tree():
    if not os.path.exists(SYLLABUS_PATH):
        return {}
    try:
        with open(SYLLABUS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading syllabus tree: {e}")
        return {}

def get_current_syllabus_state(profile):
    syllabus_tree = load_syllabus_tree()
    progress = profile.get("syllabus_progress", {}) if profile else {}
    
    current_level = progress.get("current_level", profile.get("cefr_level", "A1") if profile else "A1")
    mod_idx = progress.get("current_module_index", 0)
    top_idx = progress.get("current_topic_index", 0)
    rep_count = progress.get("repetition_count", 0)
    revision_topic = progress.get("revision_topic", None)

    level_data = syllabus_tree.get(current_level, {})
    modules = level_data.get("modules", [])
    
    current_module = modules[mod_idx] if mod_idx < len(modules) else (modules[-1] if modules else {})
    topics = current_module.get("topics", [])
    current_topic = topics[top_idx] if top_idx < len(topics) else (topics[-1] if topics else {})
    
    target_reps = current_topic.get("target_repetitions", 3)

    return {
        "current_level": current_level,
        "module_id": current_module.get("id", "M1"),
        "module_title": current_module.get("title", "Foundations"),
        "topic_id": current_topic.get("id", "T1"),
        "topic_name": current_topic.get("name", "Basics"),
        "grammar_target": current_topic.get("grammar_target", "Basic French"),
        "tenses_unlocked": current_topic.get("tenses_unlocked", ["Présent"]),
        "repetition_count": rep_count,
        "target_repetitions": target_reps,
        "revision_topic": revision_topic,
        "is_level_complete": (mod_idx >= len(modules) - 1 and top_idx >= len(topics) - 1 and rep_count >= target_reps)
    }

def record_target_usage(profile):
    """
    Increments repetition_count for the current topic.
    If target_repetitions reached, advances topic or module index.
    Returns (updated_profile, advanced_topic, level_completed).
    """
    if not profile:
        profile = {}
        
    syllabus_tree = load_syllabus_tree()
    progress = profile.get("syllabus_progress", {
        "current_level": profile.get("cefr_level", "A1"),
        "current_module_index": 0,
        "current_topic_index": 0,
        "repetition_count": 0,
        "target_repetitions": 3,
        "revision_topic": None
    })

    current_level = progress.get("current_level", "A1")
    mod_idx = progress.get("current_module_index", 0)
    top_idx = progress.get("current_topic_index", 0)
    rep_count = progress.get("repetition_count", 0) + 1

    level_data = syllabus_tree.get(current_level, {})
    modules = level_data.get("modules", [])
    current_module = modules[mod_idx] if mod_idx < len(modules) else {}
    topics = current_module.get("topics", [])
    current_topic = topics[top_idx] if top_idx < len(topics) else {}
    target_reps = current_topic.get("target_repetitions", 3)

    advanced_topic = False
    level_completed = False

    if rep_count >= target_reps:
        rep_count = 0
        advanced_topic = True
        top_idx += 1
        if top_idx >= len(topics):
            top_idx = 0
            mod_idx += 1
            if mod_idx >= len(modules):
                mod_idx = len(modules) - 1
                top_idx = len(topics) - 1
                level_completed = True

    progress["current_module_index"] = mod_idx
    progress["current_topic_index"] = top_idx
    progress["repetition_count"] = rep_count
    profile["syllabus_progress"] = progress

    return profile, advanced_topic, level_completed

def set_revision_topic(profile, revision_topic_name):
    if not profile:
        profile = {}
    progress = profile.get("syllabus_progress", {})
    progress["revision_topic"] = revision_topic_name
    profile["syllabus_progress"] = progress
    return profile

def clear_revision_topic(profile):
    if not profile:
        profile = {}
    progress = profile.get("syllabus_progress", {})
    progress["revision_topic"] = None
    profile["syllabus_progress"] = progress
    return profile

def promote_cefr_level(profile):
    levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
    current_lvl = profile.get("cefr_level", "A1")
    if current_lvl in levels:
        idx = levels.index(current_lvl)
        if idx < len(levels) - 1:
            next_lvl = levels[idx + 1]
            profile["cefr_level"] = next_lvl
            profile["syllabus_progress"] = {
                "current_level": next_lvl,
                "current_module_index": 0,
                "current_topic_index": 0,
                "repetition_count": 0,
                "target_repetitions": 3,
                "revision_topic": None
            }
    return profile
