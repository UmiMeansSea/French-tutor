import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text
from rich.theme import Theme
from rich.progress import Progress, BarColumn, TextColumn

# Rich Theme Palette Configuration
custom_theme = Theme({
    "clara.title": "bold pink1",
    "clara.border": "deep_pink3",
    "clara.accent": "magenta1",
    "derek.title": "bold bright_cyan",
    "derek.border": "dodger_blue1",
    "derek.accent": "light_slate_blue",
    "alice.title": "bold medium_purple1",
    "alice.border": "purple3",
    "alice.accent": "gold1",
    "status.text": "italic dim cyan",
    "cmd.tag": "bold yellow"
})

console = Console(theme=custom_theme)

def get_mentor_theme(mentor_style):
    s_clean = str(mentor_style).lower()
    if "derek" in s_clean or "coach" in s_clean or "strict" in s_clean:
        return {
            "name": "Derek",
            "avatar": "🎩 Derek (Strict Teacher)",
            "title_style": "derek.title",
            "border_style": "derek.border",
            "accent_style": "derek.accent",
            "badge_color": "cyan",
            "spinner": "dots"
        }
    elif "alice" in s_clean or "storyteller" in s_clean or "story" in s_clean:
        return {
            "name": "Alice",
            "avatar": "📚 Alice (Bibliophile)",
            "title_style": "alice.title",
            "border_style": "alice.border",
            "accent_style": "alice.accent",
            "badge_color": "purple",
            "spinner": "dots2"
        }
    else:
        return {
            "name": "Clara",
            "avatar": "🌸 Clara (Expat Friend)",
            "title_style": "clara.title",
            "border_style": "clara.border",
            "accent_style": "clara.accent",
            "badge_color": "magenta",
            "spinner": "bouncingBar"
        }

def render_top_dashboard(user_level, mentor_style, profile, rpg_stats=None):
    theme = get_mentor_theme(mentor_style)
    grid = Table.grid(expand=True)
    grid.add_column(justify="left")
    grid.add_column(justify="right")

    left_text = (
        f"[{theme['title_style']}]Active Mentor:[/{theme['title_style']}] {theme['avatar']}\n"
        f"[bold gold1]CEFR Target Level:[/bold gold1] [black on gold1] {user_level} [/black on gold1]"
    )

    right_text = (
        f"[bold cyan]Mode:[bold cyan] Conversational French Learning\n"
        f"[dim white]Spaced Repetition & Memory Active[/dim white]"
    )

    grid.add_row(left_text, right_text)

    panel = Panel(
        grid,
        title="[bold white]✨ EMPATHETIC AI FRENCH TUTOR OS ✨[/bold white]",
        subtitle=f"[dim]Session Active • Persona: {theme['name']}[/dim]",
        border_style=theme["border_style"],
        box=box.ROUNDED,
        padding=(0, 1)
    )
    console.print(panel)

def render_command_dashboard():
    table = Table(
        title="⚡ SYSTEM COMMAND DASHBOARD ⚡",
        box=box.ROUNDED,
        header_style="bold cyan",
        border_style="dim blue",
        expand=True
    )
    table.add_column("Command", style="bold yellow", width=14)
    table.add_column("Description & Synergy", style="white")
    table.add_column("Category", style="dim cyan", width=16)

    table.add_row("/call", "Toggle Hands-Free Continuous VAD Voice Call Mode", "🎙️ Audio / Voice")
    table.add_row("/vault", "Review Saved Vocabulary Words & Translations in SQLite", "📚 Vocabulary Vault")
    table.add_row("/notepad", "View Persistent Mentor Grammar & Vocabulary Corrections", "📝 Mentor Notepad")
    table.add_row("/dossier", "View Active Mentor Notes & Improvement Targets", "📋 Mentor Dossier")
    table.add_row("/hangout", "Launch Mentor-Specific Relaxed Hangout Session", "☕ Study Hangout")
    table.add_row("/roleplay", "Select Real-World Interactive Roleplay Scenario", "🎭 Simulation")
    table.add_row("/shadow", "Start Pronunciation & Liaison Echo Practice Drill", "🗣️ Audio Drill")
    table.add_row("/story", "Read Daily French Reading Passage & Answer Q&A", "📚 Comprehension")
    table.add_row("/profile", "Switch Active Mentor Persona (Clara, Derek, Alice)", "🔄 Persona Swap")
    table.add_row("/speed", "Toggle Turtle Mode 🐢 / Normal Pace 🐇", "🐢 Pacing Control")

    console.print(Panel(table, border_style="dim blue", box=box.ROUNDED, padding=(0, 0)))

def render_vault_dashboard(vault_rows):
    table = Table(
        title="📚 VOCABULARY VAULT (SQLITE STORED TERMS) 📚",
        box=box.ROUNDED,
        header_style="bold gold1",
        border_style="purple3",
        expand=True
    )
    table.add_column("Word / Phrase", style="bold white", width=22)
    table.add_column("Translation & Context", style="cyan")
    table.add_column("CEFR Level", style="bold yellow", justify="center", width=12)
    table.add_column("Date Added", style="dim white", justify="right", width=18)

    if not vault_rows:
        table.add_row("No words saved yet", "Chat with your mentor to automatically build your vault!", "A1", "-")
    else:
        for row in vault_rows:
            word, trans, lvl, dt = row
            dt_str = str(dt)[:10] if dt else "-"
            table.add_row(word, trans, lvl, dt_str)

    panel = Panel(table, border_style="purple3", box=box.ROUNDED, padding=(0, 1))
    console.print(panel)

def render_notepad_dashboard(notepad_rows):
    table = Table(
        title="📝 MENTOR CORRECTION NOTEPAD (SQLITE PERSISTED) 📝",
        box=box.ROUNDED,
        header_style="bold magenta",
        border_style="deep_pink3",
        expand=True
    )
    table.add_column("Date / Mentor", style="bold cyan", width=18)
    table.add_column("Original Input", style="bold red", width=22)
    table.add_column("Corrected Phrase", style="bold green", width=24)
    table.add_column("Grammar Rule & Context", style="bold yellow")

    if not notepad_rows:
        table.add_row("-", "No corrections logged", "Good job! Keep practicing!", "No mistakes recorded yet.")
    else:
        for row in notepad_rows:
            # row: id, timestamp, mentor_name, user_input, correction, rule
            _, dt, mentor, user_inp, corr, rule = row
            dt_str = f"{str(dt)[:10]} ({mentor or 'Mentor'})"
            table.add_row(dt_str, user_inp, corr, rule)

    panel = Panel(table, border_style="deep_pink3", box=box.ROUNDED, padding=(0, 1))
    console.print(panel)

def render_mentor_dialogue(parsed, mentor_style):
    theme = get_mentor_theme(mentor_style)
    import json
    import re

    if isinstance(parsed, str):
        raw_str = str(parsed).strip()
        cleaned = raw_str.replace("```json", "").replace("```", "").strip()
        try:
            parsed = json.loads(cleaned)
        except Exception:
            match = re.search(r'\{.*\}', raw_str, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                except Exception:
                    parsed = {"french_response": cleaned}
            else:
                parsed = {"french_response": cleaned}

    french_text = parsed.get("french_response", "") if isinstance(parsed, dict) else str(parsed)
    if not french_text or not str(french_text).strip() or str(french_text).strip() in ["{}", "null"]:
        french_text = "Coucou ! Enchantée ! Comment puis-je t'aider aujourd'hui ?"

    feedback = parsed.get("mentor_feedback") if isinstance(parsed, dict) else None
    phonetics = parsed.get("phonetic_breakdown") if isinstance(parsed, dict) else None
    adaptation = parsed.get("internal_adaptation_level") if isinstance(parsed, dict) else None

    content_table = Table.grid(expand=True)
    content_table.add_column()

    # Main French Response
    content_table.add_row(f"[bold white font_size=14]💬 {french_text}[/bold white font_size=14]\n")

    # Phonetics / Liaisons sub-block
    if phonetics:
        ph_panel = Panel(
            f"[bold violet]🗣️ Phonetics & Liaisons:[/bold violet] [italic text_color=purple]{phonetics}[/italic text_color]",
            border_style="purple3",
            box=box.ROUNDED,
            padding=(0, 1)
        )
        content_table.add_row(ph_panel)

    # Dedicated Mentor Notes & Tips Panel
    if feedback and str(feedback).strip():
        fb_panel = Panel(
            f"[bold yellow]{feedback}[/bold yellow]",
            title="[bold yellow]💡 Mentor Notes & Tips[/bold yellow]",
            border_style="yellow",
            box=box.ROUNDED,
            padding=(0, 1)
        )
        content_table.add_row(fb_panel)

    # Internal Level Adaptation Footer
    if adaptation:
        content_table.add_row(f"[dim italic text_color=cyan]*(Internal Level Adaptation: {adaptation})*[/dim italic text_color=cyan]")

    main_panel = Panel(
        content_table,
        title=f"[{theme['title_style']}] {theme['avatar']} [/{theme['title_style']}]",
        border_style=theme["border_style"],
        box=box.ROUNDED,
        padding=(1, 2)
    )
    console.print(main_panel)

def render_rich_dossier(mentor_style, user_profile=None):
    theme = get_mentor_theme(mentor_style)
    style_clean = mentor_style.lower()
    
    if "derek" in style_clean or "coach" in style_clean or "strict" in style_clean:
        backstory = "Mid-30s strict academic teacher. Traditional French native speaker with pristine English used rarely. Deep, serious, fair, and meticulous."
        perks = "Boosts Wit & Knowledge. Grants Red Pen Amnesty passes & University Courtyard Hangouts."
        improvements = [
            "Subjunctive mood triggers (il faut que...)",
            "Accent placement consistency (é, è, ê, ç)",
            "Formal inversion in questions (Avez-vous...)"
        ]
    elif "alice" in style_clean or "storyteller" in style_clean or "story" in style_clean:
        backstory = "Late-20s eclectic bibliophile and companion. Devours novels, history, and legends. Expressive French speaker with eccentric charm."
        perks = "Boosts Courage & Knowledge. Unlocks Secret Archives & Antiquarian Bookstore Hangouts."
        improvements = [
            "Classical literary idioms & adjectival agreement",
            "Historical context of French literature",
            "Expressive vocabulary range"
        ]
    else:
        backstory = "American expat in her early 20s living in France. Speaks French fluently with a subtle American accent. Relatable, carefree, soothing, and quirky."
        perks = "Boosts Charm & Knowledge. Unlocks Indie Record Store & Park Bench Hangouts."
        improvements = [
            "Passé composé vs. Imparfait distinction",
            "Informal texting slang & fillers (du coup, bah)",
            "Liaison blending in 'les amis' [lez-ami]"
        ]

    table = Table.grid(expand=True)
    table.add_column()

    table.add_row(f"[bold cyan]📖 Backstory:[/bold cyan] {backstory}\n")
    table.add_row(f"[bold gold1]🌟 Synergy Perks:[/bold gold1] {perks}\n")
    table.add_row("[bold magenta]🎯 WHAT TO IMPROVE (GRAMMAR & VOCAB TARGETS):[/bold magenta]")
    for idx, imp in enumerate(improvements, 1):
        table.add_row(f"  [yellow]{idx}.[/yellow] {imp}")

    panel = Panel(
        table,
        title=f"[{theme['title_style']}] 📋 MENTOR DOSSIER & FEEDBACK • {theme['name']} [/{theme['title_style']}]",
        border_style=theme["border_style"],
        box=box.ROUNDED,
        padding=(1, 2)
    )
    console.print(panel)

def status_spinner(text, mentor_style="clara"):
    theme = get_mentor_theme(mentor_style)
    return console.status(f"[{theme['title_style']}]{text}[/{theme['title_style']}]", spinner=theme["spinner"])
