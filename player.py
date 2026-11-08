"""player.py - The hero: stats, levelling, equipment bonuses, skills, saving/loading."""
from entity import Combatant
from inventory import Inventory
from quest import QuestLog, QUESTS, MAIN_QUEST_ID
from skill import SKILL_CLASSES, create_skill
from ui import C, paint, gold, xp, bar, header, rule, info, skill_name, quest_text, dim

MAX_LEVEL = 15


class Player(Combatant):
    def __init__(self, name):
        super().__init__(name, max_hp=50, attack=8, defense=2)
        self.level = 1
        self.xp = 0
        self.gold = 30
        self.kills = 0
        self.steps = 0
        self.won = False
        self.inventory = Inventory()
        self.skills = {}                 # skill_id -> Skill instance
        self.quests = QuestLog()
        self.map_id = "village"
        self.x = 0
        self.y = 0

    @classmethod
    def new(cls, name):
        """Fresh level-1 hero with starter gear and the Power Strike skill."""
        player = cls(name)
        for item_id in ("rusty_sword", "cloth_tunic"):
            player.inventory.add(item_id)
            player.inventory.equip(player, item_id)
        player.inventory.add("health_potion", 3)
        player.learn_skill("power_strike")
        return player

    # ---- derived stats -------------------------------------------------------
    @property
    def attack(self):
        weapon = self.inventory.equipped_item("weapon")
        return self.base_attack + (weapon.bonus if weapon else 0)

    @property
    def defense(self):
        armor = self.inventory.equipped_item("armor")
        return super().defense + (armor.bonus if armor else 0)

    @property
    def xp_to_next(self):
        return 25 * self.level + 5 * self.level ** 2

    # ---- progression ---------------------------------------------------------
    def gain_xp(self, amount):
        """Add XP, apply any level-ups and return message lines."""
        msgs = []
        if self.level >= MAX_LEVEL:
            return msgs
        self.xp += amount
        while self.level < MAX_LEVEL and self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.max_hp += 15
            self.base_attack += 3
            self.base_defense += 1
            self.hp = self.max_hp
            msgs.append(paint(f"  *** LEVEL UP! You are now level {self.level}! "
                              f"(+15 HP, +3 ATK, +1 DEF - fully healed) ***", C.BRIGHT_YELLOW, C.BOLD))
        if self.level >= MAX_LEVEL:
            self.xp = 0
        return msgs

    def learn_skill(self, skill_id):
        if skill_id in self.skills or skill_id not in SKILL_CLASSES:
            return False
        self.skills[skill_id] = create_skill(skill_id)
        return True

    def reset_combat_state(self):
        self.clear_effects()
        for skill in self.skills.values():
            skill.reset()

    # ---- display -------------------------------------------------------------
    def show_sheet(self):
        header(f"{self.name} - Character Sheet")
        print(f"  Level {paint(self.level, C.BRIGHT_WHITE, C.BOLD)}"
              f"   Gold: {gold(self.gold)}   Monsters slain: {self.kills}")
        print(f"  HP  {bar(self.hp, self.max_hp, 24)} {self.hp}/{self.max_hp}")
        if self.level >= MAX_LEVEL:
            print(f"  XP  {bar(1, 1, 24, C.BRIGHT_CYAN)} MAX LEVEL")
        else:
            print(f"  XP  {bar(self.xp, self.xp_to_next, 24, C.BRIGHT_CYAN)} "
                  f"{xp(f'{self.xp}/{self.xp_to_next}')}")
        print(f"  Attack: {self.attack} (base {self.base_attack})    "
              f"Defense: {self.defense} (base {self.base_defense})")
        rule()
        print("  Equipment:")
        self.inventory.show_equipment()
        rule()
        print("  Skills:")
        for skill in self.skills.values():
            print(f"   - {skill_name(skill.name)} (cooldown {skill.cooldown}): {dim(skill.description)}")
        rule()
        stage = self.quests.main_stage()
        main = QUESTS[MAIN_QUEST_ID]
        if self.won:
            print(quest_text("  Main quest: COMPLETE - the Lich King is no more!"))
        else:
            print(quest_text(f"  Main quest: step {min(stage + 1, len(main.steps))}/{len(main.steps)}"))
            obj = self.quests.objective_text(self, MAIN_QUEST_ID)
            if obj:
                print(f"   > {obj}")
        items = sum(self.inventory.items.values())
        print(f"  Items carried: {items}   (open the inventory with 'i')")

    def show_skills(self):
        header("Skills")
        for skill in self.skills.values():
            print(f"  {skill_name(skill.name)}  [{skill.status()}]")
            print(f"     {dim(skill.description)} Cooldown: {skill.cooldown} turns.")
        info("  Learn more skills from Master Kael in the village.")

    # ---- persistence ---------------------------------------------------------
    def to_dict(self):
        return {
            "name": self.name, "level": self.level, "xp": self.xp,
            "hp": self.hp, "max_hp": self.max_hp,
            "base_attack": self.base_attack, "base_defense": self.base_defense,
            "gold": self.gold, "kills": self.kills, "steps": self.steps, "won": self.won,
            "inventory": self.inventory.to_dict(),
            "skills": list(self.skills),
            "quests": self.quests.to_dict(),
            "map": self.map_id, "x": self.x, "y": self.y,
        }

    @classmethod
    def from_dict(cls, data):
        player = cls(data["name"])
        player.level = int(data["level"])
        player.xp = int(data["xp"])
        player.max_hp = int(data["max_hp"])
        player.hp = max(1, min(int(data["hp"]), player.max_hp))
        player.base_attack = int(data["base_attack"])
        player.base_defense = int(data["base_defense"])
        player.gold = int(data["gold"])
        player.kills = int(data.get("kills", 0))
        player.steps = int(data.get("steps", 0))
        player.won = bool(data.get("won", False))
        player.inventory = Inventory.from_dict(data.get("inventory", {}))
        for skill_id in data.get("skills", []):
            player.learn_skill(skill_id)
        player.quests = QuestLog.from_dict(data.get("quests", {}))
        player.map_id = data.get("map", "village")
        player.x = int(data.get("x", 0))
        player.y = int(data.get("y", 0))
        return player
