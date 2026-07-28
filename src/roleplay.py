ROLEPLAY_SCENARIOS = {
    "1": {
        "title": "Café / Restaurant 🥐",
        "description": "Order food, ask for coffee, and request the check at a Parisian café.",
        "prompt": "SCENARIO: CAFÉ / RESTAURANT. Act out a real-world simulation at a French café. Set the scene, ask what the user wants to order, or respond as the waiter/friend at the table."
    },
    "2": {
        "title": "Travel & Transit 🚆",
        "description": "Navigate a train station, buy tickets, or ask for directions.",
        "prompt": "SCENARIO: TRAVEL & TRANSIT. Act out a real-world simulation at a train station or airport. Act as the ticket agent or helpful local giving directions."
    },
    "3": {
        "title": "Social & Small Talk ☕",
        "description": "Chat with a local about weekend plans, hobbies, and weather.",
        "prompt": "SCENARIO: SOCIAL & SMALL TALK. Act out a friendly casual chat meeting a local at a park or gathering. Ask about their hobbies, day, or plans."
    }
}

def select_roleplay_menu():
    print("\n--- Real-World Roleplay Simulations ---")
    print("1. Café / Restaurant 🥐 (Order food & drinks, ask for check)")
    print("2. Travel & Transit 🚆 (Buy train tickets, ask for directions)")
    print("3. Social & Small Talk ☕ (Meet a local, discuss hobbies & weather)")
    choice = input("Select scenario (1-3) [Default: 1]: ").strip()
    scenario = ROLEPLAY_SCENARIOS.get(choice, ROLEPLAY_SCENARIOS["1"])
    print(f"\n[Roleplay Scenario Selected: {scenario['title']}]")
    print(f"Goal: {scenario['description']}\n")
    return scenario
