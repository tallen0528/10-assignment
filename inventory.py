"""inventory.py - Item storage, equipment slots and the interactive inventory menu."""
from item import ITEMS, get_item
from ui import C, paint, gold, header, rule, error, success, warn, info, ask_int, ask_choice, pause


class Inventory:
    def __init__(self):
        self.items = {}                                   # item_id -> quantity
        self.equipped = {"weapon": None, "armor": None}   # slot -> item_id

    # ---- basic bag operations ------------------------------------------------
    def add(self, item_id, qty=1):
        self.items[item_id] = self.items.get(item_id, 0) + qty

    def count(self, item_id):
        return self.items.get(item_id, 0)

    def has(self, item_id, qty=1):
        return self.count(item_id) >= qty

    def remove(self, item_id, qty=1):
        if not self.has(item_id, qty):
            return False
        self.items[item_id] -= qty
        if self.items[item_id] <= 0:
            del self.items[item_id]
        return True

    def entries(self):
        """Sorted list of (Item, quantity) for everything in the bag."""
        return sorted(((get_item(i), q) for i, q in self.items.items()),
                      key=lambda e: (e[0].kind, e[0].name))

    def consumables(self):
        return [(i, q) for i, q in self.entries() if i.kind == "consumable"]

    def equipped_item(self, slot):
        item_id = self.equipped.get(slot)
        return get_item(item_id) if item_id else None

    # ---- equipment -----------------------------------------------------------
    def equip(self, player, item_id):
        item = get_item(item_id)
        if player.level < item.level_req:
            return f"You need to be level {item.level_req} to equip {item.name}."
        if not self.remove(item_id):
            return "You don't have that item."
        old = self.equipped[item.slot]
        if old:
            self.add(old)
        self.equipped[item.slot] = item_id
        return f"You equip {item.label()}."

    def unequip(self, slot):
        item_id = self.equipped.get(slot)
        if not item_id:
            return "Nothing is equipped in that slot."
        self.equipped[slot] = None
        self.add(item_id)
        return f"You unequip {get_item(item_id).label()}."

    # ---- interactive menu ----------------------------------------------------
    def show_equipment(self):
        for slot, label in (("weapon", "Weapon"), ("armor", "Armor ")):
            item = self.equipped_item(slot)
            text = f"{item.label()} ({item.stats().split(',')[0]})" if item else paint("none", C.GRAY)
            print(f"  {label}: {text}")

    def menu(self, player):
        """Browse the bag: use consumables, equip gear, unequip slots."""
        while True:
            header("Inventory")
            print(f"  Gold: {gold(player.gold)}    HP: {player.hp}/{player.max_hp}")
            self.show_equipment()
            rule()
            entries = self.entries()
            if not entries:
                info("  Your bag is empty.")
            for n, (item, qty) in enumerate(entries, 1):
                stats = f" [{item.stats()}]" if item.stats() else ""
                print(f"  {n}) {item.label()} x{qty}{paint(stats, C.GRAY)}  - {paint(item.description, C.GRAY)}")
            rule()
            print("  Type an item number to use/equip it, 'u' to unequip, or 0 to close.")
            choice = ask_choice_or_number("  > ", len(entries))
            if choice == 0:
                return
            if choice == "u":
                self._unequip_menu()
                continue
            item, _ = entries[choice - 1]
            self._activate(player, item)

    def _unequip_menu(self):
        slot = ask_choice("  Unequip which slot? (weapon/armor/cancel): ", ["weapon", "armor", "cancel"])
        if slot != "cancel":
            print("  " + self.unequip(slot))
            pause()

    def _activate(self, player, item):
        if item.kind == "consumable":
            if item.heal and not item.buff and player.hp >= player.max_hp:
                warn("  You're already at full health.")
            else:
                for line in item.use(player):
                    print("  " + line)
                self.remove(item.item_id)
        elif item.kind in ("weapon", "armor"):
            msg = self.equip(player, item.item_id)
            (success if msg.startswith("You equip") else error)("  " + msg)
        else:
            info(f"  {item.name}: {item.description}")
        pause()

    # ---- persistence ---------------------------------------------------------
    def to_dict(self):
        return {"items": dict(self.items), "equipped": dict(self.equipped)}

    @classmethod
    def from_dict(cls, data):
        inv = cls()
        for item_id, qty in data.get("items", {}).items():
            if item_id in ITEMS and isinstance(qty, int) and qty > 0:
                inv.items[item_id] = qty
        for slot, item_id in data.get("equipped", {}).items():
            if slot in inv.equipped and (item_id in ITEMS or item_id is None):
                inv.equipped[slot] = item_id
        return inv


def ask_choice_or_number(prompt, maximum):
    """Accept 'u' or an integer 0..maximum; keep asking on bad input."""
    from ui import ask
    while True:
        raw = ask(prompt).lower()
        if raw == "u":
            return "u"
        try:
            value = int(raw)
        except ValueError:
            error(f"  Type a number from 0 to {maximum}, or 'u'.")
            continue
        if 0 <= value <= maximum:
            return value
        error(f"  Type a number from 0 to {maximum}, or 'u'.")
