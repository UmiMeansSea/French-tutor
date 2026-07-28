def add_xp(profile, amount, reason=""):
    xp = profile.get("xp", 0) + amount
    level = (xp // 100) + 1
    profile["xp"] = xp
    profile["level"] = level
    print(f"*(+ {amount} XP earned for {reason}! Total XP: {xp} | Level {level})*")
    return profile

def check_badges(profile, session_metrics):
    badges = set(profile.get("badges", []))
    new_unlocked = []

    if session_metrics.get("total_turns", 0) >= 1 and "First Steps 🌟" not in badges:
        badges.add("First Steps 🌟")
        new_unlocked.append("First Steps 🌟")

    if session_metrics.get("shadow_completed", False) and "Liaison Legend 🗣️" not in badges:
        badges.add("Liaison Legend 🗣️")
        new_unlocked.append("Liaison Legend 🗣️")

    if session_metrics.get("roleplay_completed", False) and "Café Connoisseur 🥐" not in badges:
        badges.add("Café Connoisseur 🥐")
        new_unlocked.append("Café Connoisseur 🥐")

    if profile.get("milestone_streak", 0) >= 3 and "Streak Master 🔥" not in badges:
        badges.add("Streak Master 🔥")
        new_unlocked.append("Streak Master 🔥")

    if len(profile.get("weak_spots", [])) >= 3 and "Diagnostic Pioneer 🎯" not in badges:
        badges.add("Diagnostic Pioneer 🎯")
        new_unlocked.append("Diagnostic Pioneer 🎯")

    profile["badges"] = list(badges)
    for b in new_unlocked:
        print(f"\n🎉 UNLOCKED NEW BADGE: {b} 🎉\n")
    return profile, new_unlocked
