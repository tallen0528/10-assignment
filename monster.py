"""monster.py - Monster base class, five regular monster types and the final boss.

Every subclass has different stats, loot and a different behaviour in `act()`.
"""
import random

from entity import Combatant, compute_damage
from ui import C, paint, taken, monster_name


class Monster(Combatant):
    type_id = "monster"
    display_name = "Monster"
    BASE_HP = 20
    ATTACK = 5
    DEFENSE = 0
    XP = 10
    GOLD = (1, 5)
    DROPS = []          # list of (item_id, drop_chance)
    VARIANCE = 0.10     # +/- random spread on HP
    is_boss = False
    stun_chance = 1.0   # 1.0 = always stunnable
    flavor = "A creature blocks your path!"

    def __init__(self):
        hp = int(self.BASE_HP * random.uniform(1 - self.VARIANCE, 1 + self.VARIANCE))
        super().__init__(self.display_name, hp, self.ATTACK, self.DEFENSE)
        self.xp_reward = self.XP
        self.stolen_gold = 0

    # ---- behaviour -----------------------------------------------------------
    def strike(self, target, power_mult=1.0, verb="hits", pierce=0.0):
        """Deal damage to `target` and return the log line."""
        dmg = target.take_damage(compute_damage(self.attack * power_mult, target, pierce))
        return f"{monster_name(self.name)} {verb} you for {taken(dmg)} damage!"

    def act(self, target):
        """Take this monster's turn. Returns a list of log lines."""
        return [self.strike(target)]

    def try_revive(self):
        """Called when HP hits 0. Return a message if the monster comes back to life."""
        return None

    # ---- loot ----------------------------------------------------------------
    def roll_loot(self):
        gold = random.randint(*self.GOLD) + self.stolen_gold
        items = [item_id for item_id, chance in self.DROPS if random.random() < chance]
        return gold, items


class Slime(Monster):
    type_id = "slime"
    display_name = "Green Slime"
    BASE_HP = 24
    ATTACK = 7
    DEFENSE = 0
    XP = 10
    GOLD = (3, 8)
    DROPS = [("slime_gel", 0.55), ("health_potion", 0.08)]
    flavor = "A wobbling green blob oozes toward you."

    def act(self, target):
        return [self.strike(target, 1.0, "slams into")]


class Goblin(Monster):
    type_id = "goblin"
    display_name = "Goblin Raider"
    BASE_HP = 32
    ATTACK = 10
    DEFENSE = 1
    XP = 16
    GOLD = (6, 14)
    DROPS = [("goblin_ear", 0.50), ("health_potion", 0.12)]
    flavor = "A goblin cackles and waves a jagged knife."

    def act(self, target):
        msgs = [self.strike(target, 1.0, "stabs")]
        if target.gold > 0 and random.random() < 0.25:
            stolen = min(target.gold, random.randint(3, 8))
            target.gold -= stolen
            self.stolen_gold += stolen
            msgs.append(paint(f"The goblin snatches {stolen} gold from your pouch! (Defeat it to get it back)", C.YELLOW))
        return msgs


class Wolf(Monster):
    type_id = "wolf"
    display_name = "Dire Wolf"
    BASE_HP = 46
    ATTACK = 15
    DEFENSE = 3
    XP = 24
    GOLD = (8, 18)
    DROPS = [("wolf_pelt", 0.55), ("health_potion", 0.10)]
    flavor = "Yellow eyes glint in the grass - a dire wolf growls!"

    def act(self, target):
        if random.random() < 0.30:
            return [self.strike(target, 0.7, "bites"), self.strike(target, 0.7, "bites again,")]
        return [self.strike(target, 1.0, "lunges and bites")]


class Skeleton(Monster):
    type_id = "skeleton"
    display_name = "Crypt Skeleton"
    BASE_HP = 80
    ATTACK = 25
    DEFENSE = 10
    XP = 40
    GOLD = (15, 30)
    DROPS = [("ancient_bone", 0.55), ("greater_potion", 0.10), ("ironbark_tonic", 0.10)]
    flavor = "Bones clatter together as a skeleton lurches out of the dark."

    def __init__(self):
        super().__init__()
        self.revived = False

    def act(self, target):
        return [self.strike(target, 1.0, "rakes you with rusted claws, dealing")]

    def try_revive(self):
        if self.revived:
            return None
        self.revived = True
        self.hp = max(1, int(self.max_hp * 0.3))
        return paint("The bones rattle and knit back together - the skeleton rises again!", C.YELLOW)


class Orc(Monster):
    type_id = "orc"
    display_name = "Ashen Orc"
    BASE_HP = 110
    ATTACK = 29
    DEFENSE = 10
    XP = 60
    GOLD = (25, 45)
    DROPS = [("orc_tusk", 0.55), ("greater_potion", 0.18), ("orc_cleaver", 0.04)]
    flavor = "An ash-grey orc bellows and raises a spiked club."

    def act(self, target):
        if random.random() < 0.30:
            return [paint("The orc roars and winds up a SAVAGE SMASH!", C.BRIGHT_RED),
                    self.strike(target, 1.7, "crushes you with a smash, dealing")]
        return [self.strike(target, 1.0, "clubs")]


class Boss(Monster):
    """Bosses are tougher, have fixed HP, cannot be fled from and resist stuns."""
    is_boss = True
    VARIANCE = 0.0
    stun_chance = 0.4


class LichKing(Boss):
    type_id = "lich_king"
    display_name = "Lich King Morvath"
    BASE_HP = 520
    ATTACK = 36
    DEFENSE = 13
    XP = 600
    GOLD = (250, 300)
    DROPS = [("greater_potion", 1.0), ("knights_blade", 0.5)]
    flavor = "The Lich King rises from his throne, green fire pouring from empty eye sockets."

    def __init__(self):
        super().__init__()
        self.turn = 0
        self.enraged = False

    def act(self, target):
        self.turn += 1
        msgs = []
        if not self.enraged and self.hp < self.max_hp * 0.4:
            self.enraged = True
            self.base_attack = int(self.base_attack * 1.25)
            msgs.append(paint("Morvath howls - dark power surges through him! He is ENRAGED!", C.BRIGHT_RED, C.BOLD))
        if self.turn % 5 == 0:
            msgs.append(paint("Morvath conjures a BONE CAGE around you!", C.MAGENTA))
            msgs.append(self.strike(target, 0.5, "crushes you with the cage, dealing"))
            target.add_effect("stun", 1)
            return msgs
        roll = random.random()
        if roll < 0.30:
            msgs.append(self.strike(target, 1.3, "hurls a SHADOW BOLT, dealing", pierce=0.6))
        elif roll < 0.50:
            dmg = target.take_damage(compute_damage(self.attack * 0.9, target))
            healed_amt = self.heal(dmg // 2)
            msgs.append(f"{monster_name(self.name)} drains your soul for {taken(dmg)} damage "
                        f"and heals {healed_amt} HP!")
        else:
            msgs.append(self.strike(target, 1.0, "rakes you with spectral claws, dealing"))
        return msgs


MONSTER_CLASSES = {cls.type_id: cls for cls in (Slime, Goblin, Wolf, Skeleton, Orc, LichKing)}

# which monsters roam each zone, with spawn weights
ZONE_TABLE = {
    "forest": [(Slime, 45), (Goblin, 30), (Wolf, 25)],
    "crypt": [(Skeleton, 55), (Orc, 45)],
}


def spawn_monster(zone):
    """Pick a random monster for a zone using the weights above."""
    classes, weights = zip(*ZONE_TABLE[zone])
    return random.choices(classes, weights=weights, k=1)[0]()
