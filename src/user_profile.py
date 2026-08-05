import os
import json

PROFILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "user_profile.json")

DEFAULT_SYLLABUS_PROGRESS = {
    "current_level": "A1",
    "current_module_index": 0,
    "current_topic_index": 0,
    "repetition_count": 0,
    "target_repetitions": 3,
    "revision_topic": None
}

def load_profile():
    if not os.path.exists(PROFILE_PATH):
        return None
    try:
        with open(PROFILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading profile: {e}")
        return None

def save_profile(cefr_level, mentor_style, weak_spots=None, user_memories=None, syllabus_progress=None):
    if weak_spots is None:
        weak_spots = []
    existing = load_profile() or {}
    existing["cefr_level"] = cefr_level
    existing["mentor_style"] = mentor_style
    if user_memories is not None:
        existing["user_memories"] = user_memories
    if syllabus_progress is not None:
        existing["syllabus_progress"] = syllabus_progress
    elif "syllabus_progress" not in existing:
        existing["syllabus_progress"] = DEFAULT_SYLLABUS_PROGRESS.copy()
    
    current_spots = existing.get("weak_spots", [])
    for spot in weak_spots:
        if spot and spot not in current_spots:
            current_spots.append(spot)
    existing["weak_spots"] = current_spots
    
    os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
    try:
        with open(PROFILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving profile: {e}")
        return False
