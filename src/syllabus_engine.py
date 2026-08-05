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

def save_syllabus_tree(tree):
    try:
        os.makedirs(os.path.dirname(SYLLABUS_PATH), exist_ok=True)
        with open(SYLLABUS_PATH, 'w', encoding='utf-8') as f:
            json.dump(tree, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving syllabus tree: {e}")
        return False

def get_current_syllabus_state(profile, mentor_style="clara"):
    syllabus_tree = load_syllabus_tree()
    dept_key = mentor_style.lower()
    if "derek" in dept_key or "strict" in dept_key:
        dept_key = "derek"
    elif "alice" in dept_key or "story" in dept_key:
        dept_key = "alice"
    else:
        dept_key = "clara"

    departments = syllabus_tree.get("departments", {})
    dept_data = departments.get(dept_key, {})
    active_level = dept_data.get("active_level", "A2")
    levels = dept_data.get("levels", {})
    level_obj = levels.get(active_level, {})
    modules = level_obj.get("modules", [])

    # Find active in_progress or first not_started module
    active_mod = None
    for mod in modules:
        if mod.get("status") in ["in_progress", "not_started"]:
            active_mod = mod
            break
    if not active_mod and modules:
        active_mod = modules[-1]

    if not active_mod:
        active_mod = {"id": "M1", "topic": "General Practice", "reps_required": 5, "reps_completed": 0, "status": "in_progress"}

    reps_completed = active_mod.get("reps_completed", 0)
    reps_required = active_mod.get("reps_required", 5)

    return {
        "user_current_level": syllabus_tree.get("user_current_level", active_level),
        "department_key": dept_key,
        "department_name": dept_data.get("name", "General Studies"),
        "active_level": active_level,
        "module_id": active_mod.get("id"),
        "topic_name": active_mod.get("topic"),
        "reps_completed": reps_completed,
        "reps_required": reps_required,
        "bookmarked_revision": dept_data.get("bookmarked_revision"),
        "is_level_complete": (level_obj.get("status") == "completed")
    }

def record_target_usage(profile, mentor_style="clara"):
    """
    Increments reps_completed for the active module in syllabus_tracker.json.
    Returns (updated_profile, advanced_module, level_completed).
    """
    syllabus_tree = load_syllabus_tree()
    dept_key = mentor_style.lower()
    if "derek" in dept_key or "strict" in dept_key:
        dept_key = "derek"
    elif "alice" in dept_key or "story" in dept_key:
        dept_key = "alice"
    else:
        dept_key = "clara"

    departments = syllabus_tree.get("departments", {})
    dept_data = departments.get(dept_key, {})
    active_level = dept_data.get("active_level", "A2")
    level_obj = dept_data.get("levels", {}).get(active_level, {})
    modules = level_obj.get("modules", [])

    advanced_module = False
    level_completed = False

    for mod in modules:
        if mod.get("status") in ["in_progress", "not_started"]:
            mod["status"] = "in_progress"
            mod["reps_completed"] = mod.get("reps_completed", 0) + 1
            if mod["reps_completed"] >= mod.get("reps_required", 5):
                mod["status"] = "completed"
                advanced_module = True
            break

    # Check if all modules in active level are completed
    if modules and all(m.get("status") == "completed" for m in modules):
        level_obj["status"] = "completed"
        level_completed = True

    save_syllabus_tree(syllabus_tree)
    return profile, advanced_module, level_completed

def set_revision_topic(profile, mentor_style, revision_topic_name):
    syllabus_tree = load_syllabus_tree()
    dept_key = mentor_style.lower()
    if "derek" in dept_key: dept_key = "derek"
    elif "alice" in dept_key: dept_key = "alice"
    else: dept_key = "clara"

    if "departments" in syllabus_tree and dept_key in syllabus_tree["departments"]:
        syllabus_tree["departments"][dept_key]["bookmarked_revision"] = revision_topic_name
        save_syllabus_tree(syllabus_tree)
    return profile

def clear_revision_topic(profile, mentor_style):
    return set_revision_topic(profile, mentor_style, None)

def promote_cefr_level(profile, mentor_style="clara"):
    levels_order = ["A1", "A2", "B1", "B2", "C1", "C2"]
    syllabus_tree = load_syllabus_tree()
    dept_key = mentor_style.lower()
    if "derek" in dept_key: dept_key = "derek"
    elif "alice" in dept_key: dept_key = "alice"
    else: dept_key = "clara"

    dept_data = syllabus_tree.get("departments", {}).get(dept_key, {})
    curr_lvl = dept_data.get("active_level", "A2")
    if curr_lvl in levels_order:
        idx = levels_order.index(curr_lvl)
        if idx < len(levels_order) - 1:
            next_lvl = levels_order[idx + 1]
            dept_data["active_level"] = next_lvl
            if next_lvl in dept_data.get("levels", {}):
                dept_data["levels"][next_lvl]["status"] = "in_progress"
            save_syllabus_tree(syllabus_tree)
            if profile:
                profile["cefr_level"] = next_lvl
    return profile
