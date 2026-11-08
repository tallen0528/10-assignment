"""game.py - The game session: exploration loop, commands, travel, encounters, boss fight and saving."""
import random
import re

import story
from combat import Combat
from map import build_world
from monster import LichKing, spawn_monster
from npc import NPCS
from player import Player
from quest import QuestLog, QUESTS, MAIN_QUEST_ID
from ui import (C, paint, clear, header, rule, bar, gold, xp, quest_text, narrate, info, warn, error,
                success, dim, ask, ask_int, ask_yes_no, pause)

DIRS = {"w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0)}
HERO_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z '\-]{1,15}$")
BOSS_STEP = next(i for i, s in enumerate(QUESTS[MAIN_QUEST_ID].steps) if s["kind"] == "boss")

HELP = """\
  Movement : w/a/s/d (you can chain moves, e.g. 'ddd'). Walk into an NPC to talk, into a number to travel.
  t        : talk to an adjacent NPC          i : inventory (use/equip items)
  c        : character sheet & progress       k : skills
  q        : quest log                        save : save now (the game also autosaves)
  x        : save and return to the main menu h : this help
  Tips     : ',' ground in the forest/crypt hides monsters, '.' paths are safe.
             Buy gear from Brom, learn skills from Kael, heal with Sister Elara."""


class Game:
    def __init__(self, db, username):
        self.db = db
        self.username = username
        self.world = build_world()
        self.player = None
        self.running = True
        self.messages = []

    # ---- helpers -------------------------------------------------------------
    @property
    def current_map(self):
        return self.world[self.player.map_id]

    @property
    def boss_alive(self):
        return not self.player.won

    def notify(self, text, color=C.YELLOW):
        self.messages.append(paint(text, color))

    def autosave(self):
        if self.player is not None:
            self.db.save_game(self.username, self.player.to_dict())

    # ---- startup -------------------------------------------------------------
    def start(self):
        """Load the saved hero or create a new one. Returns False if the player backed out."""
        data = self.db.load_game(self.username)
        if data:
            try:
                self.player = Player.from_dict(data)
            except (KeyError, TypeError, ValueError, AttributeError) as exc:
                error(f"Your save file could not be read ({exc!r}).")
                if not ask_yes_no("Start a brand new hero? (this overwrites the damaged save)"):
                    return False
                data = None
            else:
                self._fix_position()
                success(f"Loaded {self.player.name} (level {self.player.level}). Continuing your adventure...")
                pause()
                return True
        self._new_game()
        return True

    def _new_game(self):
        clear()
        header("Create your hero")
        while True:
            name = ask(f"  Hero name (Enter = '{self.username}'): ") or self.username
            if HERO_NAME_RE.match(name):
                break
            error("  Names are 2-16 characters: letters, spaces, apostrophes or hyphens, starting with a letter.")
        self.player = Player.new(name)
        self.player.quests.start(MAIN_QUEST_ID)
        village = self.world["village"]
        self.player.map_id = "village"
        self.player.x, self.player.y = village.spawn
        story.show_intro(name)
        print(quest_text("  Quest started: " + QUESTS[MAIN_QUEST_ID].title))
        print(quest_text("  Objective: " + QUESTS[MAIN_QUEST_ID].steps[0]["desc"]))
        info("  Look for the blue 'A' - that's Elder Alden. Type 'h' any time for help.")
        pause()
        self.autosave()

    def _fix_position(self):
        """Make sure a loaded position is valid (guards against edited/corrupt saves)."""
        p = self.player
        m = self.world.get(p.map_id)
        if m is None or not m.is_walkable(p.x, p.y):
            p.map_id = "village"
            p.x, p.y = self.world["village"].spawn

    # ---- main loop -----------------------------------------------------------
    def run(self):
        if not self.start():
            return
        try:
            while self.running:
                self.draw()
                self.handle(ask("> ").lower())
                self.autosave()
        except (KeyboardInterrupt, EOFError):
            print()
        finally:
            self.autosave()
            success("Progress saved. See you next time, hero!")

    def draw(self):
        clear()
        p, m = self.player, self.current_map
        zone = paint("[monsters roam here]", C.BRIGHT_RED) if m.zone else paint("[safe]", C.BRIGHT_GREEN)
        header(f"{m.name}  {zone}")
        print(f"  {paint(p.name, C.BRIGHT_GREEN, C.BOLD)}  Lv {p.level}   "
              f"HP {bar(p.hp, p.max_hp, 14)} {p.hp}/{p.max_hp}   "
              f"XP {bar(p.xp, p.xp_to_next, 10, C.BRIGHT_CYAN)} {p.xp}/{p.xp_to_next}   {gold(p.gold)}")
        if p.won:
            print(quest_text("  Main quest complete - the Lich King is defeated. Explore freely!"))
        else:
            print(quest_text("  Quest: " + p.quests.objective_text(p, MAIN_QUEST_ID)))
        rule()
        print(m.render(p.x, p.y, self.boss_alive))
        rule()
        print("  " + self._legend())
        print(dim("  [w/a/s/d] move  [t] talk  [i] inventory  [c] character  [k] skills  [q] quests  [x] exit  [h] help"))
        for line in self.messages:
            print("  " + line)
        self.messages.clear()

    def _legend(self):
        m = self.current_map
        parts = [paint("@", C.BRIGHT_GREEN, C.BOLD) + " you"]
        for ch, npc_id in m.npc_chars.items():
            parts.append(paint(ch, C.BRIGHT_BLUE, C.BOLD) + f" {NPCS[npc_id].name}")
        for ch, portal in m.portals.items():
            parts.append(paint(ch, C.BRIGHT_MAGENTA, C.BOLD) + f" exit to {portal['label']}")
        if m.map_id == "crypt" and self.boss_alive:
            parts.append(paint("X", C.BRIGHT_RED, C.BOLD) + " Lich King's lair")
        return "   ".join(parts)

    # ---- command handling ----------------------------------------------------
    def handle(self, cmd):
        p = self.player
        if not cmd:
            return
        if all(ch in DIRS for ch in cmd):
            for key in cmd[:12]:
                if self.move(key):
                    break
        elif cmd in ("t", "talk"):
            self.talk_nearby()
        elif cmd in ("i", "inv", "inventory"):
            clear()
            p.inventory.menu(p)
        elif cmd in ("c", "char", "character", "stats"):
            clear()
            p.show_sheet()
            pause()
        elif cmd in ("k", "skills"):
            clear()
            p.show_skills()
            pause()
        elif cmd in ("q", "quests", "log"):
            clear()
            p.quests.show(p)
            pause()
        elif cmd in ("h", "help", "?"):
            clear()
            header("Help")
            print(HELP)
            pause()
        elif cmd == "save":
            self.autosave()
            self.notify("Game saved.", C.BRIGHT_GREEN)
        elif cmd in ("x", "exit", "quit"):
            if ask_yes_no("Save and return to the main menu?"):
                self.running = False
        else:
            self.notify(f"Unknown command '{cmd}'. Type 'h' for help.", C.BRIGHT_RED)

    # ---- movement ------------------------------------------------------------
    def move(self, key):
        """Try to move one tile. Returns True if something interrupted multi-step movement."""
        p, m = self.player, self.current_map
        dx, dy = DIRS[key]
        nx, ny = p.x + dx, p.y + dy
        tile = m.tile_at(nx, ny)

        npc_id = m.npc_at(nx, ny)
        if npc_id:
            self.talk_to(npc_id)
            return True
        portal_key, portal = m.portal_at(nx, ny)
        if portal:
            self.use_portal(portal)
            return True
        if tile == "X" and self.boss_alive:
            self.boss_encounter()
            return True
        if not (m.is_walkable(nx, ny) or tile == "X"):
            self.notify(f"You can't go that way - {m.describe_tile(tile)} blocks the path.")
            return True

        p.x, p.y = nx, ny
        p.steps += 1
        if p.steps % 3 == 0 and p.hp < p.max_hp:
            p.heal(1)                                   # slow natural regeneration
        if m.is_danger(nx, ny) and random.random() < m.encounter_rate:
            self.fight(spawn_monster(m.zone))
            return True
        return False

    def use_portal(self, portal):
        p = self.player
        need = portal.get("requires")
        if need and not p.inventory.has(need):
            self.notify(portal.get("locked", "The way is locked."), C.BRIGHT_RED)
            return
        origin = p.map_id
        dest = self.world[portal["to"]]
        p.map_id = dest.map_id
        p.x, p.y = dest.arrival_point(origin)
        clear()
        header(f"Entering: {dest.name}", C.BRIGHT_MAGENTA)
        narrate(dest.intro)
        events = p.quests.on_visit(p, dest.map_id)
        if events:
            print()
            QuestLog.print_events(events)
        pause()
        self.autosave()

    # ---- NPCs ----------------------------------------------------------------
    def talk_nearby(self):
        p = self.player
        nearby = self.current_map.adjacent_npcs(p.x, p.y)
        if not nearby:
            self.notify("There is nobody close enough to talk to. Stand next to an NPC (or walk into them).")
        elif len(nearby) == 1:
            self.talk_to(nearby[0])
        else:
            for n, npc_id in enumerate(nearby, 1):
                print(f"  {n}) {NPCS[npc_id].name}")
            self.talk_to(nearby[ask_int("  Talk to who? ", 1, len(nearby)) - 1])

    def talk_to(self, npc_id):
        clear()
        NPCS[npc_id].talk(self)
        pause()

    # ---- combat --------------------------------------------------------------
    def fight(self, monster):
        result = Combat(self.player, monster).run()
        self._after_combat(monster, result)
        pause()

    def _after_combat(self, monster, result):
        p = self.player
        if result == "win":
            p.kills += 1
            events = (p.quests.on_boss(p, monster) if monster.is_boss
                      else p.quests.on_kill(p, monster, p.map_id))
            if events:
                print()
                QuestLog.print_events(events)
            if monster.is_boss:
                self._victory()
        elif result == "lose":
            self._defeat()

    def boss_encounter(self):
        p = self.player
        if p.quests.main_stage() < BOSS_STEP:
            self.notify("A seal of dark magic blocks the throne room. Defeat the Crypt's guardians first "
                        "(check your quest log with 'q').", C.BRIGHT_RED)
            return
        clear()
        header("The Throne Room", C.BRIGHT_RED)
        narrate("A sea of candles flickers around a throne of black bone. The Lich King Morvath "
                "turns his burning gaze upon you. 'Another hero come to die,' he whispers.")
        print()
        if ask_yes_no("Step forward and face Morvath? (there is no escape once the battle begins)"):
            self.fight(LichKing())

    def _defeat(self):
        p = self.player
        lost = p.gold // 10
        p.gold -= lost
        p.hp = max(1, p.max_hp // 2)
        p.map_id = "village"
        p.x, p.y = self.world["village"].spawn
        p.clear_effects()
        print()
        narrate("Darkness takes you... You wake in Willowbrook with Sister Elara bandaging your wounds.")
        print(paint(f"  You lost {lost} gold and wake at half health.", C.YELLOW))
        self.autosave()

    def _victory(self):
        p = self.player
        p.won = True
        self.autosave()
        pause()
        story.show_ending(p.name)
        if not ask_yes_no("Keep exploring the world of Eldoria?"):
            self.running = False
