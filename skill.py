"""skill.py - Skill base class plus learnable skills. Each subclass has its own effect and cooldown."""
import random

from entity import compute_damage
from ui import skill_name, dealt, healed, paint, C


class Skill:
    skill_id = "skill"
    name = "Skill"
    description = ""
    cooldown = 2        # turns before the skill can be used again
    level_req = 1       # level needed to learn it from the trainer
    cost = 0            # gold price at the trainer
    trainable = True    # False = can only be gained as a quest reward

    def __init__(self):
        self.current_cd = 0

    @property
    def ready(self):
        return self.current_cd <= 0

    def start_cooldown(self):
        self.current_cd = self.cooldown

    def tick(self):
        if self.current_cd > 0:
            self.current_cd -= 1

    def reset(self):
        self.current_cd = 0

    def status(self):
        return "ready" if self.ready else f"cooldown {self.current_cd}"

    def use(self, user, target):
        """Apply the effect and return a list of combat log messages."""
        raise NotImplementedError


class PowerStrike(Skill):
    skill_id = "power_strike"
    name = "Power Strike"
    description = "A crushing blow dealing 180% weapon damage."
    cooldown = 2
    level_req = 1
    cost = 0

    def use(self, user, target):
        dmg = target.take_damage(compute_damage(user.attack * 1.8, target))
        return [f"{skill_name(self.name)}! You smash {target.name} for {dealt(dmg)} damage."]


class Heal(Skill):
    skill_id = "heal"
    name = "Heal"
    description = "Restore 25% of your max HP plus a little extra."
    cooldown = 4
    level_req = 2
    cost = 60

    def use(self, user, target):
        amount = user.heal(int(user.max_hp * 0.25) + 15 + getattr(user, "level", 1) * 2)
        return [f"{skill_name(self.name)}! Warm light mends your wounds (+{healed(amount)} HP)."]


class Fireball(Skill):
    skill_id = "fireball"
    name = "Fireball"
    description = "Magic flames that ignore 70% of the enemy's defense."
    cooldown = 3
    level_req = 3
    cost = 90

    def use(self, user, target):
        power = 14 + getattr(user, "level", 1) * 3 + user.attack * 0.9
        dmg = target.take_damage(compute_damage(power, target, pierce=0.7))
        return [f"{skill_name(self.name)}! Flames engulf {target.name} for {dealt(dmg)} damage."]


class IronSkin(Skill):
    skill_id = "iron_skin"
    name = "Iron Skin"
    description = "Harden your body: big defense bonus for 3 turns."
    cooldown = 5
    level_req = 4
    cost = 110

    def use(self, user, target):
        bonus = 5 + getattr(user, "level", 1)
        user.add_effect("guard", 3, bonus)
        return [f"{skill_name(self.name)}! Your skin turns to metal (+{bonus} DEF for 3 turns)."]


class VenomStrike(Skill):
    skill_id = "venom_strike"
    name = "Venom Strike"
    description = "A poisoned slash: normal damage, then poison for 4 turns."
    cooldown = 4
    level_req = 5
    cost = 140
    trainable = False   # reward from Ranger Lyra's side quest

    def use(self, user, target):
        dmg = target.take_damage(compute_damage(user.attack * 1.0, target))
        poison = 3 + getattr(user, "level", 1)
        target.add_effect("poison", 4, poison)
        return [f"{skill_name(self.name)}! You cut {target.name} for {dealt(dmg)} and inject "
                f"{paint(f'{poison} poison/turn', C.MAGENTA)}."]


class Thunderclap(Skill):
    skill_id = "thunderclap"
    name = "Thunderclap"
    description = "Lightning for 150% damage that may stun the enemy for a turn."
    cooldown = 6
    level_req = 6
    cost = 220

    def use(self, user, target):
        dmg = target.take_damage(compute_damage(user.attack * 1.5, target))
        msgs = [f"{skill_name(self.name)}! Lightning strikes {target.name} for {dealt(dmg)} damage."]
        if random.random() < getattr(target, "stun_chance", 1.0):
            target.add_effect("stun", 1)
            msgs.append(f"{target.name} is stunned!")
        else:
            msgs.append(f"{target.name} shrugs off the stun!")
        return msgs


SKILL_CLASSES = {cls.skill_id: cls for cls in
                 (PowerStrike, Heal, Fireball, IronSkin, VenomStrike, Thunderclap)}


def create_skill(skill_id):
    """Instantiate a skill by id (raises KeyError for unknown ids)."""
    return SKILL_CLASSES[skill_id]()
