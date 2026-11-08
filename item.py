"""item.py - Item classes (consumables, equipment, loot) and the master item catalogue."""
from ui import C, paint, healed


class Item:
    kind = "item"
    color = C.WHITE

    def __init__(self, item_id, name, description, price=0, sellable=True):
        self.item_id = item_id
        self.name = name
        self.description = description
        self.price = price
        self.sellable = sellable

    @property
    def sell_price(self):
        return self.price // 2 if self.sellable else 0

    def label(self):
        """Item name in its category colour."""
        return paint(self.name, self.color)

    def stats(self):
        return ""

    def use(self, user):
        return [f"{self.name} can't be used right now."]


class Consumable(Item):
    kind = "consumable"
    color = C.GREEN

    def __init__(self, item_id, name, description, price, heal=0, buff=None):
        super().__init__(item_id, name, description, price)
        self.heal = heal
        self.buff = buff  # (effect_name, value, turns)

    def stats(self):
        parts = []
        if self.heal:
            parts.append(f"+{self.heal} HP")
        if self.buff:
            parts.append(f"+{self.buff[1]} DEF for {self.buff[2]} turns")
        return ", ".join(parts)

    def use(self, user):
        msgs = []
        if self.heal:
            amount = user.heal(self.heal)
            msgs.append(f"You use {self.label()} and recover {healed(amount)} HP.")
        if self.buff:
            effect, value, turns = self.buff
            user.add_effect(effect, turns, value)
            msgs.append(f"You use {self.label()}. Your skin hardens (+{value} DEF for {turns} turns).")
        return msgs


class Equipment(Item):
    slot = ""

    def __init__(self, item_id, name, description, price, bonus, level_req=1):
        super().__init__(item_id, name, description, price)
        self.bonus = bonus
        self.level_req = level_req


class Weapon(Equipment):
    kind = "weapon"
    slot = "weapon"
    color = C.BRIGHT_WHITE

    def stats(self):
        return f"+{self.bonus} ATK, needs Lv {self.level_req}"


class Armor(Equipment):
    kind = "armor"
    slot = "armor"
    color = C.BRIGHT_BLUE

    def stats(self):
        return f"+{self.bonus} DEF, needs Lv {self.level_req}"


class Material(Item):
    """Monster loot that can be sold or handed in for quests."""
    kind = "material"
    color = C.GRAY


class QuestItem(Item):
    kind = "quest"
    color = C.ORANGE

    def __init__(self, item_id, name, description):
        super().__init__(item_id, name, description, price=0, sellable=False)


def _build_catalogue():
    items = [
        Consumable("health_potion", "Health Potion", "A red tonic. Restores 40 HP.", 25, heal=40),
        Consumable("greater_potion", "Greater Health Potion", "A glowing crimson elixir. Restores 100 HP.", 70, heal=100),
        Consumable("ironbark_tonic", "Ironbark Tonic", "Bitter bark brew that hardens your skin.", 40, buff=("guard", 6, 4)),

        Weapon("rusty_sword", "Rusty Sword", "Better than a stick. Barely.", 20, 2, 1),
        Weapon("iron_sword", "Iron Sword", "A dependable blade from Brom's forge.", 90, 5, 2),
        Weapon("steel_sword", "Steel Sword", "Well balanced, keen edged.", 240, 9, 4),
        Weapon("orc_cleaver", "Orc Cleaver", "Crude, heavy and brutally effective.", 300, 12, 6),
        Weapon("knights_blade", "Knight's Blade", "Forged for kings. Hums faintly.", 520, 14, 7),

        Armor("cloth_tunic", "Cloth Tunic", "Offers comfort, not protection.", 10, 1, 1),
        Armor("leather_armor", "Leather Armor", "Boiled leather, supple and light.", 70, 3, 2),
        Armor("chainmail", "Chainmail", "Thousands of tiny rings.", 180, 6, 3),
        Armor("plate_armor", "Plate Armor", "A walking fortress of steel.", 450, 10, 6),

        Material("slime_gel", "Slime Gel", "Sticky gel. Healers love it.", 10),
        Material("goblin_ear", "Goblin Ear", "Gross, but someone pays for it.", 14),
        Material("wolf_pelt", "Wolf Pelt", "Thick grey fur. Warm.", 24),
        Material("ancient_bone", "Ancient Bone", "Cold to the touch.", 36),
        Material("orc_tusk", "Orc Tusk", "A yellowed trophy.", 50),

        QuestItem("crypt_key", "Crypt Key", "A heavy iron key that opens the Ashen Crypt."),
    ]
    return {i.item_id: i for i in items}


ITEMS = _build_catalogue()


def get_item(item_id):
    """Look up an item by id (raises KeyError for unknown ids)."""
    return ITEMS[item_id]
