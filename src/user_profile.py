import os
import json

PROFILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "user_profile.json")

def load_profile():
    if not os.path.exists(PROFILE_PATH):
        return None
    try:
        with open(PROFILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading profile: {e}")
        return None

def save_profile(cefr_level, mentor_style, milestone_streak=0, weak_spots=None):
    if weak_spots is None:
        weak_spots = []
    existing = load_profile() or {}
    existing["cefr_level"] = cefr_level
    existing["mentor_style"] = mentor_style
    existing["milestone_streak"] = milestone_streak
    
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
