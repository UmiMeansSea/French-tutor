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

def save_profile(cefr_level, mentor_style):
    profile = {
        "cefr_level": cefr_level,
        "mentor_style": mentor_style
    }
    # Ensure db directory exists
    os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
    try:
        with open(PROFILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving profile: {e}")
        return False
