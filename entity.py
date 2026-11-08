"""entity.py - Base class shared by everything that can fight (Player and Monster)."""
import random

from ui import C, paint


def compute_damage(power, target, pierce=0.0):
    """Damage of an attack with `power` against `target`.

    Half of the target's defense is subtracted; `pierce` (0.0-1.0) ignores that share of it.
    """
    raw = power * random.uniform(0.9, 1.1)
    mitigation = target.defense * (1.0 - pierce) / 2
    return max(1, int(raw - mitigation))


class Combatant:
    """HP, attack/defense and temporary status effects (poison, guard, stun)."""

    EFFECT_NAMES = {"poison": "Poisoned", "guard": "Guarded", "stun": "Stunned"}

    def __init__(self, name, max_hp, attack, defense):
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        self.base_attack = attack
        self.base_defense = defense
        self.effects = {}

    # Subclasses (Player) extend these to include equipment.
    @property
    def attack(self):
        return self.base_attack

    @property
    def defense(self):
        return self.base_defense + self.effect_value("guard")

    def is_alive(self):
        return self.hp > 0

    def take_damage(self, amount):
        amount = max(0, int(amount))
        self.hp = max(0, self.hp - amount)
        return amount

    def heal(self, amount):
        amount = max(0, min(int(amount), self.max_hp - self.hp))
        self.hp += amount
        return amount

    # ---- status effects ------------------------------------------------------
    def add_effect(self, name, turns, value=0):
        self.effects[name] = {"turns": turns, "value": value}

    def has_effect(self, name):
        return name in self.effects

    def effect_value(self, name):
        return self.effects.get(name, {}).get("value", 0)

    def clear_effects(self):
        self.effects.clear()

    def effects_text(self):
        return " ".join(
            paint(f"[{self.EFFECT_NAMES.get(n, n)} {e['turns']}t]", C.MAGENTA)
            for n, e in self.effects.items()
        )

    def start_turn(self):
        """Apply poison, detect stun and tick effect timers. Returns (messages, skip_turn)."""
        msgs, skip = [], False
        poison = self.effects.get("poison")
        if poison:
            dmg = self.take_damage(poison["value"])
            msgs.append(paint(f"{self.name} takes {dmg} poison damage.", C.MAGENTA))
        if "stun" in self.effects:
            skip = True
            msgs.append(paint(f"{self.name} is stunned and loses the turn!", C.YELLOW))
        for key in list(self.effects):
            self.effects[key]["turns"] -= 1
            if self.effects[key]["turns"] <= 0:
                del self.effects[key]
                if key == "guard":
                    msgs.append(paint(f"{self.name}'s defensive boost wears off.", C.GRAY))
        return msgs, skip
