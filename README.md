# The Shadow Over Willowbrook

A terminal RPG in Python. Explore three tile maps, talk to five NPCs, finish a six-step main quest,
and defeat the Lich King Morvath to win. Accounts and progress are stored with TinyDB, so you can
quit, log back in and continue where you left off.

## Run it

```
pip install -r requirements.txt     # installs TinyDB
python main.py                      # Python 3.8+
```

Use a terminal that supports ANSI colours (Windows Terminal, macOS Terminal, any Linux terminal).
Set `NO_COLOR=1` to turn colours off.

## Controls

| Key | Action |
|-----|--------|
| `w` `a` `s` `d` | Move (chain them, e.g. `dddd`). Walk into an NPC to talk, into a number to travel |
| `t` | Talk to an adjacent NPC |
| `i` | Inventory: use potions, equip or unequip gear |
| `c` | Character sheet: level, HP/XP bars, gold, stats, equipment, skills, quest progress |
| `k` | Skills and cooldowns |
| `q` | Quest log |
| `save` | Save now (the game also autosaves after every command) |
| `x` | Save and return to the main menu |

## Colour legend

green = healing / healthy HP, bright yellow = gold, cyan = XP, bright blue = NPCs,
red = monsters and damage taken, orange = quests, purple = skills, magenta = exits.

## Walkthrough

**Main quest, "The Shadow Over Willowbrook" (6 steps)**
1. Talk to Elder Alden (`A`) in the village.
2. Defeat 5 monsters in the Whispering Forest (east gate, `1`).
3. Find Ranger Lyra (`L`) in the forest; she gives you the Crypt Key.
4. Enter the Ashen Crypt through the iron door (`2`, south-east of the forest).
5. Defeat 4 monsters inside the Crypt.
6. Defeat the Lich King Morvath at the red `X`. Winning ends the game (you may keep exploring).

**Side quests**
- *Herbal Remedy*: Sister Elara wants 3 Slime Gel. Reward: gold, XP, potions.
- *Pelts for Brom*: Brom wants 3 Wolf Pelts. Reward: gold, XP, Chainmail.
- *Goblin Menace*: Ranger Lyra wants 4 Goblin Raiders dead. Reward: gold, XP, the Venom Strike skill.

**NPCs**: Elder Alden (lore and hints), Brom (shop, buys loot), Sister Elara (paid healing),
Master Kael (teaches skills), Ranger Lyra (forest scout).

**Monsters**: Green Slime, Goblin Raider (steals gold), Dire Wolf (double bites), Crypt Skeleton
(revives once), Ashen Orc (savage smash), plus the boss Lich King Morvath (life drain, bone cage, enrage).
Monsters drop gold and items; `,` tiles in the forest and crypt hide monsters, `.` paths are safe.

**Skills** (each with its own effect and cooldown): Power Strike (start), Heal, Fireball (ignores
most defense), Iron Skin (defense buff), Venom Strike (poison), Thunderclap (stun).
Buy them from Master Kael as your level allows.

## Files

| File | Purpose |
|------|---------|
| `main.py` | Entry point: title screen, login / register menu |
| `auth.py` | Registration and login (salted PBKDF2 password hashes, input validation) |
| `database.py` | TinyDB accounts + saves, corrupt-file recovery |
| `game.py` | Game session: exploration loop, commands, travel, encounters, boss fight |
| `player.py` | Player stats, levelling, skills, save/load |
| `entity.py` | `Combatant` base class (HP, defense, poison/guard/stun effects) |
| `monster.py` | `Monster` -> `Slime`, `Goblin`, `Wolf`, `Skeleton`, `Orc`; `Boss` -> `LichKing` |
| `skill.py` | `Skill` -> `PowerStrike`, `Heal`, `Fireball`, `IronSkin`, `VenomStrike`, `Thunderclap` |
| `combat.py` | Turn-based battle loop |
| `inventory.py` | Bag, equipment slots, inventory menu |
| `item.py` | Item classes and the item catalogue |
| `quest.py` | Quest data and the quest log tracker |
| `npc.py` | The five NPCs and their dialogue and services |
| `shop.py` | Buy and sell system |
| `map.py` | The three maps and their rendering |
| `story.py` | Title art, opening story and ending |
| `ui.py` | Colours, formatting and validated input helpers |

Save data lives in `data/rpg_db.json` (created on first run). Delete that file to reset everything.
