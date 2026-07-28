MENTOR_STAT_WEIGHTS = {
    "clara": {"Charm": 1.5, "Knowledge": 1.5, "Wit": 1.2, "Courage": 1.0, "Memory": 0.8},
    "derek": {"Wit": 1.5, "Knowledge": 1.2, "Courage": 1.0, "Memory": 1.0, "Charm": 0.8},
    "alice": {"Courage": 1.5, "Knowledge": 1.5, "Charm": 1.2, "Wit": 1.0, "Memory": 1.0}
}

DEFAULT_STATS = {
    "Knowledge": 15,
    "Charm": 15,
    "Wit": 15,
    "Courage": 15,
    "Memory": 15
}

def award_stat_xp(stats, stat_name, base_amount, mentor_style):
    if not stats:
        stats = DEFAULT_STATS.copy()
        
    style_key = "clara"
    s_clean = mentor_style.lower()
    if "derek" in s_clean or "coach" in s_clean or "strict" in s_clean:
        style_key = "derek"
    elif "alice" in s_clean or "story" in s_clean:
        style_key = "alice"
        
    multiplier = MENTOR_STAT_WEIGHTS.get(style_key, {}).get(stat_name, 1.0)
    gained = int(base_amount * multiplier)
    stats[stat_name] = stats.get(stat_name, 0) + gained
    return stats, gained

def get_stat_level(stat_val):
    return (stat_val // 20) + 1

def render_stat_chart(stats, active_mentor="Clara"):
    try:
        from rich_ui import render_rich_stat_chart
        render_rich_stat_chart(stats, active_mentor)
    except Exception:
        if not stats:
            stats = DEFAULT_STATS.copy()
            
        print("\n╔════════════════════════════════════════════════════════════╗")
        print("║               📊 RPG PERSONA STAT CHART 📊                 ║")
        print("╠════════════════════════════════════════════════════════════╣")
        
        stat_icons = {
            "Knowledge": "🧠",
            "Charm":     "✨",
            "Wit":       "⚡",
            "Courage":   "🦁",
            "Memory":    "💾"
        }
        
        for stat, val in stats.items():
            lvl = get_stat_level(val)
            progress_in_lvl = (val % 20) / 20.0
            filled = int(progress_in_lvl * 10)
            bar = "█" * filled + "░" * (10 - filled)
            icon = stat_icons.get(stat, "⭐")
            print(f"║ {icon} {stat:<10} [{bar}] Lvl {lvl:<2} ({val} PTS)")
            
        print("╠════════════════════════════════════════════════════════════╣")
        print(f"║ 🎭 Active Mentor Synergy: {active_mentor:<30} ║")
        print("╚════════════════════════════════════════════════════════════╝\n")
