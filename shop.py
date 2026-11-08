"""shop.py - The merchant's shop: buy items with gold and sell loot back."""
from item import get_item
from ui import C, paint, gold, header, rule, info, error, success, warn, ask_int, pause


class Shop:
    def __init__(self, name, stock):
        self.name = name
        self.stock = stock      # list of item ids always in stock

    def open(self, player):
        while True:
            header(self.name, C.BRIGHT_YELLOW)
            print(f"  Your gold: {gold(player.gold)}")
            print("  1) Buy    2) Sell    0) Leave")
            choice = ask_int("  > ", 0, 2)
            if choice == 0:
                return
            if choice == 1:
                self._buy(player)
            else:
                self._sell(player)

    # ---- buying --------------------------------------------------------------
    def _buy(self, player):
        header("For Sale", C.BRIGHT_YELLOW)
        for n, item_id in enumerate(self.stock, 1):
            item = get_item(item_id)
            stats = item.stats() or item.description
            print(f"  {n:>2}) {item.label():<30} {gold(item.price):>14}   {paint(stats, C.GRAY)}")
        print("   0) Back")
        choice = ask_int("  Buy which item? ", 0, len(self.stock))
        if choice == 0:
            return
        item = get_item(self.stock[choice - 1])
        if item.price > player.gold:
            error(f"  You can't afford {item.name} (need {item.price}g, you have {player.gold}g).")
            return
        max_afford = player.gold // item.price
        if item.kind in ("weapon", "armor"):
            qty = 1
        else:
            qty = ask_int(f"  How many? (1-{min(99, max_afford)}, or 0 to cancel): ", 0, min(99, max_afford))
            if qty == 0:
                return
        total = item.price * qty
        player.gold -= total
        player.inventory.add(item.item_id, qty)
        success(f"  Bought {qty}x {item.name} for {total}g.")
        if item.kind in ("weapon", "armor"):
            info("  (Open your inventory with 'i' to equip it.)")

    # ---- selling -------------------------------------------------------------
    def _sell(self, player):
        entries = [(i, q) for i, q in player.inventory.entries() if i.sellable]
        if not entries:
            warn("  You have nothing the merchant wants.")
            return
        header("Sell Items", C.BRIGHT_YELLOW)
        for n, (item, qty) in enumerate(entries, 1):
            print(f"  {n:>2}) {item.label():<30} x{qty:<3} sells for {gold(item.sell_price)} each")
        print("   0) Back")
        choice = ask_int("  Sell which item? ", 0, len(entries))
        if choice == 0:
            return
        item, have = entries[choice - 1]
        qty = ask_int(f"  How many? (1-{have}, or 0 to cancel): ", 0, have)
        if qty == 0:
            return
        player.inventory.remove(item.item_id, qty)
        total = item.sell_price * qty
        player.gold += total
        success(f"  Sold {qty}x {item.name} for {total}g.")
