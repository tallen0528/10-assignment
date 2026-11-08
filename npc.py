"""npc.py - Five NPCs, each with their own personality, dialogue and special service.

    ElderAlden   - village elder: lore + guidance (main quest giver)
    MerchantBrom - runs the shop, side quest "Pelts for Brom"
    HealerElara  - heals you for gold, side quest "Herbal Remedy"
    TrainerKael  - teaches new skills for gold
    RangerLyra   - lives in the forest, gives the Crypt Key, side quest "Goblin Menace"
"""
import random

from item import get_item
from quest import QuestLog, QUESTS, MAIN_QUEST_ID
from shop import Shop
from skill import SKILL_CLASSES
from ui import (C, paint, say, gold, header, rule, info, warn, error, success, quest_text,
                ask_int, ask_yes_no, pause, npc_name, skill_name, dim)


class NPC:
    npc_id = "npc"
    name = "Villager"
    title = ""
    chat_lines = ["Hello there."]
    farewell = "Safe travels."

    def __init__(self):
        self._last_line = None

    def say(self, text):
        say(self.name, text)

    # ---- conversation flow ---------------------------------------------------
    def talk(self, game):
        player = game.player
        print()
        header(f"{self.name} - {self.title}", C.BRIGHT_BLUE)
        events = player.quests.on_talk(player, self.npc_id)
        if events:
            QuestLog.print_events(events, speaker=self.name)
            game.autosave()
        else:
            self.say(self.greeting(player))
        while True:
            options = self.options(game)
            rule()
            for n, (label, _) in enumerate(options, 1):
                print(f"  {n}) {label}")
            print("  0) Say goodbye")
            choice = ask_int("  > ", 0, len(options))
            if choice == 0:
                self.say(self.farewell)
                return
            options[choice - 1][1](game)
            game.autosave()

    def greeting(self, player):
        return random.choice(self.chat_lines)

    def options(self, game):
        """Menu entries as (label, callable). Subclasses add their own services."""
        opts = [("Chat", self.chat)]
        if any(q.giver == self.npc_id for q in QUESTS.values()):
            opts.append(("Ask about work (quests)", self.quest_menu))
        return opts

    def chat(self, game):
        choices = [l for l in self.chat_lines if l != self._last_line] or self.chat_lines
        self._last_line = random.choice(choices)
        self.say(self._last_line)

    def quest_menu(self, game):
        player = game.player
        offered = False
        for quest in QUESTS.values():
            if quest.giver != self.npc_id:
                continue
            offered = True
            status = player.quests.status(quest.qid)
            if status is None:
                self.say(quest.offer)
                print(quest_text(f"  Quest: {quest.title}"))
                print(f"  Reward: {self._reward_text(quest.reward)}")
                if ask_yes_no("  Accept this quest?"):
                    QuestLog.print_events(player.quests.start(quest.qid))
                    self.say("Good luck out there.")
            elif status == "active":
                self.say(quest.remind)
                print(quest_text(f"  > {player.quests.objective_text(player, quest.qid)}"))
            else:
                self.say(quest.thanks)
        if not offered:
            self.say("I have no work for you right now.")

    @staticmethod
    def _reward_text(reward):
        parts = []
        if reward.get("gold"):
            parts.append(gold(reward["gold"]))
        if reward.get("xp"):
            parts.append(f"{reward['xp']} XP")
        for item_id, qty in reward.get("items", {}).items():
            parts.append(f"{get_item(item_id).label()} x{qty}")
        for sid in reward.get("skills", []):
            parts.append(f"skill: {SKILL_CLASSES[sid].name}")
        return ", ".join(parts) or "none"


class ElderAlden(NPC):
    npc_id = "alden"
    name = "Elder Alden"
    title = "Village Elder"
    farewell = "May the old stones of Willowbrook guard your steps."
    chat_lines = [
        "Willowbrook has stood three hundred years. I would hate to see it become the last page of its own story.",
        "My knees ache whenever the Lich King stirs. Today, they ache terribly.",
        "Walk softly in the forest, traveler - but carry a loud sword.",
        "When I was young, the Ashen Crypt was only a ghost story for children. Children are wiser than elders, sometimes.",
    ]

    def options(self, game):
        return [("Chat", self.chat), ("Ask about the Lich King", self.lore_lich),
                ("Ask about the Ashen Crypt", self.lore_crypt), ("What should I do next?", self.hint)]

    def lore_lich(self, game):
        self.say("Morvath was a king who bargained with death and lost his heart in the trade. "
                 "Now he commands the dead and wants to turn all of Eldoria into his throne room.")

    def lore_crypt(self, game):
        self.say("The Crypt lies past the forest, behind an iron door. Skeletons and ash-orcs guard it. "
                 "Do not enter without a strong blade, good armor and a pocketful of potions.")

    def hint(self, game):
        player = game.player
        if player.won:
            self.say("You have saved us all. There is nothing more I could ask of you.")
            return
        obj = player.quests.objective_text(player, MAIN_QUEST_ID)
        self.say("Your path is clear, if not easy.")
        print(quest_text(f"  > {obj}"))


class MerchantBrom(NPC):
    npc_id = "brom"
    name = "Brom"
    title = "Merchant & Blacksmith"
    farewell = "Come back with coin, friend!"
    chat_lines = [
        "Coin talks, friend - and mine talks the loudest!",
        "Wolves keep chewing through my supply of pelts. Bad for business, good for prices.",
        "Buy a potion. Nobody ever died with too many potions. Well - nobody who'd admit it.",
        "Heavier armor, slower feet, longer life. That's the blacksmith's bargain.",
    ]

    def __init__(self):
        super().__init__()
        self.shop = Shop("Brom's Goods", [
            "health_potion", "greater_potion", "ironbark_tonic",
            "iron_sword", "steel_sword", "knights_blade",
            "leather_armor", "chainmail", "plate_armor"])

    def options(self, game):
        return [("Browse wares (shop)", self.open_shop)] + super().options(game)

    def open_shop(self, game):
        self.say("Take a look! Everything's honestly priced. Mostly.")
        self.shop.open(game.player)


class HealerElara(NPC):
    npc_id = "elara"
    name = "Sister Elara"
    title = "Village Healer"
    farewell = "Please be careful. The light go with you."
    chat_lines = [
        "I have buried too many brave faces already. Please come back from the forest in one piece.",
        "Rest is a medicine, too - but bandages cost gold, and gold doesn't grow on trees.",
        "The slimes leave a gel that breaks fevers. I never thought I'd be grateful for slime.",
        "Every night I light a candle in the window for whoever is still out there.",
    ]

    def options(self, game):
        return [("Receive healing", self.heal)] + super().options(game)

    def heal_cost(self, player):
        return 8 + 2 * player.level

    def heal(self, game):
        player = game.player
        cost = self.heal_cost(player)
        if player.hp >= player.max_hp:
            self.say("You are in perfect health, dear. Save your coin.")
        elif player.gold < cost:
            self.say(f"I'm sorry - the herbs cost {cost} gold, and you have only {player.gold}.")
        elif ask_yes_no(f"  Heal fully for {gold(cost)}?"):
            player.gold -= cost
            player.hp = player.max_hp
            success("  Warm light washes over you. HP fully restored!")
            self.say("There. Good as new.")


class TrainerKael(NPC):
    npc_id = "kael"
    name = "Master Kael"
    title = "Battle Trainer"
    farewell = "Don't die. It's bad for my reputation."
    chat_lines = [
        "Skill beats strength. Strength beats luck. Luck beats nothing at all.",
        "Cooldowns, kid. Learn them. A move you can't use is a move you don't have.",
        "I lost this eye to a skeleton. It put itself back together just to finish the job.",
        "Heal when you're at half, not when you're at one. Dead heroes make poor students.",
    ]

    def options(self, game):
        return [("Learn new skills", self.teach)] + super().options(game)

    def teach(self, game):
        player = game.player
        pool = [c for c in SKILL_CLASSES.values() if c.trainable and c.skill_id not in player.skills]
        if not pool:
            self.say("I've taught you everything I know. Now go and use it.")
            return
        self.say("Pay the fee and I'll drill it into you. Level counts, too.")
        print(f"  Your gold: {gold(player.gold)}   Your level: {player.level}")
        for n, cls in enumerate(pool, 1):
            lock = "" if player.level >= cls.level_req else paint(f"  (needs Lv {cls.level_req})", C.RED)
            print(f"  {n}) {skill_name(cls.name)} - {gold(cls.cost)}, Lv {cls.level_req}, "
                  f"cooldown {cls.cooldown}{lock}")
            print(f"       {dim(cls.description)}")
        print("  0) Back")
        choice = ask_int("  Learn which skill? ", 0, len(pool))
        if choice == 0:
            return
        cls = pool[choice - 1]
        if player.level < cls.level_req:
            self.say(f"Come back at level {cls.level_req}. You're not ready.")
        elif player.gold < cls.cost:
            self.say(f"That costs {cls.cost} gold. You're short.")
        else:
            player.gold -= cls.cost
            player.learn_skill(cls.skill_id)
            success(f"  You learned {cls.name}!")
            self.say("Good. Don't forget the cooldown.")


class RangerLyra(NPC):
    npc_id = "lyra"
    name = "Ranger Lyra"
    title = "Forest Ranger"
    farewell = "Stay quiet. Stay alive."
    chat_lines = [
        "Quiet. The goblins hear everything except good sense.",
        "Wolves hunt by smell; skeletons don't breathe. Different enemies, different tactics.",
        "Past the south-eastern gate lies the Crypt. I wouldn't go... but then, I'm not the chosen one.",
        "The trees were never this restless before Morvath woke up.",
    ]


NPCS = {cls.npc_id: cls() for cls in (ElderAlden, MerchantBrom, HealerElara, TrainerKael, RangerLyra)}
