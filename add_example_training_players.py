#!/usr/bin/env python3
"""
Add 100 example players to the KVK Training system
"""
import sqlite3
import random

DATABASE = 'kvk.db'

# List of example names
NAMES = [
    "Rydak", "Joy", "Shadow", "Dragon", "Phoenix", "Thor", "Zeus", "Odin", "Loki", "Freya",
    "Atlas", "Titan", "Apollo", "Ares", "Hades", "Poseidon", "Athena", "Artemis", "Hera", "Demeter",
    "Viking", "Samurai", "Knight", "Warrior", "Gladiator", "Spartan", "Centurion", "Legion", "Paladin", "Crusader",
    "Storm", "Thunder", "Lightning", "Blaze", "Inferno", "Frost", "Ice", "Glacier", "Avalanche", "Tsunami",
    "Wolf", "Bear", "Lion", "Tiger", "Eagle", "Hawk", "Falcon", "Panther", "Cobra", "Viper",
    "Reaper", "Assassin", "Hunter", "Ranger", "Scout", "Sniper", "Soldier", "Commander", "General", "Admiral",
    "Phantom", "Ghost", "Specter", "Wraith", "Shade", "Spirit", "Soul", "Demon", "Angel", "Saint",
    "Blade", "Sword", "Axe", "Hammer", "Spear", "Arrow", "Bow", "Shield", "Armor", "Helm",
    "King", "Queen", "Prince", "Princess", "Duke", "Baron", "Lord", "Lady", "Knight", "Noble",
    "Mystic", "Wizard", "Mage", "Sorcerer", "Warlock", "Witch", "Sage", "Oracle", "Prophet", "Seer"
]

# List of alliance codes (3 letters)
ALLIANCES = [
    "KVK", "WAR", "LDR", "KNG", "GOD", "ICE", "FIR", "STM", "DRK", "LGT",
    "WLF", "BER", "LGN", "TIT", "PHX", "DRG", "THR", "ZUS", "ODN", "LKI"
]

def add_example_players():
    """Add 100 example players with random power and alliances"""
    print("🔧 Adding 100 example players...")
    
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    
    # Clear existing training players
    cur.execute('DELETE FROM training_players;')
    print("  ✓ Cleared existing players")
    
    # Add 100 players
    for i in range(100):
        name = random.choice(NAMES) + str(random.randint(1, 999))
        power = round(random.uniform(20.0, 80.0), 1)  # Power between 20M and 80M
        alliance = random.choice(ALLIANCES)
        
        cur.execute(
            'INSERT INTO training_players (name, power, alliance, team) VALUES (?, ?, ?, ?);',
            (name, power, alliance, 0)  # Team 0 = unassigned
        )
    
    conn.commit()
    conn.close()
    
    print("✅ Successfully added 100 example players!")
    print("🔄 Visit /kvk-training and click 'Rebalance Teams' to assign them")

if __name__ == '__main__':
    add_example_players()
