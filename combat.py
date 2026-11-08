"""combat.py - Turn-based combat between the player and one monster.

Each round: player acts (attack / skill / item / flee), then the monster acts.
Skill cooldowns tick at the start of each of the player's turns.
"""
import random

from entity import compute_damage
from item import get_item
from ui import (C, paint, bar, rule, header, gold, xp, monster_name, dealt, taken,
                skill_name, ask_int, error, warn, info, pause)


class Combat:
    def __init__(self, player, monster):
        self.player = player
        self.monster = monster

    # ---- main loop -----------------------------------------------------------
    def run(self):
        """Fight until someone falls. Returns 'win', 'lose' or 'flee'."""
        p, m = self.player, self.monster
        p.reset_combat_state()
        print()
        header("BATTLE!", C.BRIGHT_RED)
        print(paint(m.flavor, C.ITALIC))
        print(f"A wild {monster_name(m.name)} appears!")

        while True:
            # --- player's turn ---
            msgs, stunned = p.start_turn()
            self._print(msgs)
            for skill in p.skills.values():
                skill.tick()
            if not p.is_alive():
                return self._defeat()
            if not m.is_alive():
                if self._monster_down():
                    return self._victory()
            elif stunned:
                pass
            else:
                if self._player_turn() == "flee":
                    return "flee"
                if not m.is_alive() and self._monster_down():
                    return self._victory()

            # --- monster's turn ---
            if m.is_alive():
                msgs, skip = m.start_turn()
                self._print(msgs)
                if not m.is_alive():
                    if self._monster_down():
                        return self._victory()
                elif not skip:
                    self._print(m.act(p))
                if not p.is_alive():
                    return self._defeat()

    def _monster_down(self):
        """True if the monster is really dead (False when it revives)."""
        revive_msg = self.monster.try_revive()
        if revive_msg:
            print(revive_msg)
            return False
        return True

    # ---- player actions ------------------------------------------------------
    def _player_turn(self):
        p, m = self.player, self.monster
        while True:
            self._show_status()
            print("  1) Attack   2) Skill   3) Item   4) Flee")
            choice = ask_int("  Your action: ", 1, 4)
            if choice == 1:
                self._basic_attack()
                return None
            if choice == 2 and self._use_skill():
                return None
            if choice == 3 and self._use_item():
                return None
            if choice == 4:
                if m.is_boss:
                    warn("  There is no escape from this fight!")
                    continue
                if random.random() < 0.55:
                    print(paint("  You escape into the shadows!", C.GRAY))
                    return "flee"
                print(paint("  You couldn't get away!", C.YELLOW))
                return None

    def _basic_attack(self):
        p, m = self.player, self.monster
        dmg = compute_damage(p.attack, m)
        crit = random.random() < 0.10
        if crit:
            dmg = int(dmg * 1.5)
        dmg = m.take_damage(dmg)
        tag = paint(" CRITICAL HIT!", C.BRIGHT_YELLOW, C.BOLD) if crit else ""
        print(f"  You strike {monster_name(m.name)} for {dealt(dmg)} damage.{tag}")

    def _use_skill(self):
        p, m = self.player, self.monster
        skills = list(p.skills.values())
        for n, s in enumerate(skills, 1):
            state = paint("ready", C.GREEN) if s.ready else paint(s.status(), C.RED)
            print(f"   {n}) {skill_name(s.name)} [{state}] - {paint(s.description, C.GRAY)}")
        print("   0) Back")
        choice = ask_int("  Use which skill? ", 0, len(skills))
        if choice == 0:
            return False
        skill = skills[choice - 1]
        if not skill.ready:
            error(f"  {skill.name} is on cooldown for {skill.current_cd} more turn(s).")
            return False
        self._print(["  " + line for line in skill.use(p, m)])
        skill.start_cooldown()
        return True

    def _use_item(self):
        p = self.player
        usable = p.inventory.consumables()
        if not usable:
            warn("  You have no usable items.")
            return False
        for n, (item, qty) in enumerate(usable, 1):
            print(f"   {n}) {item.label()} x{qty} - {paint(item.stats(), C.GRAY)}")
        print("   0) Back")
        choice = ask_int("  Use which item? ", 0, len(usable))
        if choice == 0:
            return False
        item = usable[choice - 1][0]
        self._print(["  " + line for line in item.use(p)])
        p.inventory.remove(item.item_id)
        return True

    # ---- outcomes ------------------------------------------------------------
    def _victory(self):
        p, m = self.player, self.monster
        print()
        print(paint(f"  {m.name} is defeated!", C.BRIGHT_GREEN, C.BOLD))
        gold_drop, drops = m.roll_loot()
        p.gold += gold_drop
        print(f"  Loot: {gold(gold_drop)}   Experience: {xp(m.xp_reward)}")
        for item_id in drops:
            p.inventory.add(item_id)
            print(f"  The monster dropped: {get_item(item_id).label()}!")
        self._print(p.gain_xp(m.xp_reward))
        p.clear_effects()
        return "win"

    def _defeat(self):
        print(paint(f"\n  You collapse... {self.monster.name} stands victorious.", C.BRIGHT_RED, C.BOLD))
        self.player.clear_effects()
        return "lose"

    # ---- display -------------------------------------------------------------
    def _show_status(self):
        p, m = self.player, self.monster
        rule()
        print(f"  {paint(p.name.ljust(20), C.BRIGHT_GREEN, C.BOLD)} HP {bar(p.hp, p.max_hp)} "
              f"{p.hp}/{p.max_hp} {p.effects_text()}")
        print(f"  {monster_name(m.name.ljust(20))} HP {bar(m.hp, m.max_hp)} "
              f"{m.hp}/{m.max_hp} {m.effects_text()}")
        rule()

    @staticmethod
    def _print(lines):
        for line in lines:
            print(line)
