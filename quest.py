"""quest.py - Quest definitions (1 multi-step main quest + 3 side quests) and the QuestLog tracker.

Quests are data-driven: each quest is a list of steps. A step has a `kind`:
    talk    - speak to the NPC in `target`
    kill    - defeat `count` monsters (`target` is a monster type id or "any", optional `map`)
    collect - hand `count` of item `target` to NPC `turn_in`
    visit   - enter the map `target`
    boss    - defeat the boss whose type id is `target`
Events returned by the QuestLog are (kind, text) tuples printed by `print_events`.
"""
from item import get_item
from skill import SKILL_CLASSES
from ui import C, paint, say, narrate, quest_text, gold, xp, header, rule, info, pause

MAIN_QUEST_ID = "shadow_over_willowbrook"


class Quest:
    def __init__(self, qid, title, summary, steps, giver=None, reward=None,
                 is_main=False, offer="", remind="", thanks=""):
        self.qid = qid
        self.title = title
        self.summary = summary
        self.steps = steps
        self.giver = giver
        self.reward = reward or {}
        self.is_main = is_main
        self.offer = offer
        self.remind = remind
        self.thanks = thanks


def _build_quests():
    main = Quest(
        MAIN_QUEST_ID, "The Shadow Over Willowbrook",
        "Stop the Lich King Morvath before his undead army reaches the village.",
        is_main=True,
        steps=[
            {"kind": "talk", "target": "alden",
             "desc": "Speak with Elder Alden in Willowbrook's square.",
             "text": "Morvath, the Lich King, stirs beneath the Ashen Crypt. His shadow already poisons "
                     "the forest. Prove yourself, traveler: slay five of the creatures in the Whispering "
                     "Forest, east of the village gate. Take these potions - you'll need them.",
             "reward": {"xp": 20, "items": {"health_potion": 2}}},
            {"kind": "kill", "target": "any", "map": "forest", "count": 5,
             "desc": "Defeat monsters in the Whispering Forest",
             "text": "The beasts fall, and the forest breathes easier. Ranger Lyra patrols deeper in the "
                     "woods - she knows the road to the Crypt.",
             "reward": {"xp": 40, "gold": 40}},
            {"kind": "talk", "target": "lyra",
             "desc": "Find Ranger Lyra in the Whispering Forest.",
             "text": "So Alden sent you. Good. This key opens the iron door at the forest's south-east "
                     "edge - the Ashen Crypt. Skeletons and orcs guard the halls; at the far end, "
                     "Morvath waits. Don't go in unprepared.",
             "reward": {"xp": 50, "items": {"crypt_key": 1}}},
            {"kind": "visit", "target": "crypt",
             "desc": "Enter the Ashen Crypt through the iron door.",
             "text": "The door slams shut behind you. Cold air and the rattle of bones fill the dark.",
             "reward": {"xp": 30}},
            {"kind": "kill", "target": "any", "map": "crypt", "count": 4,
             "desc": "Defeat monsters inside the Ashen Crypt",
             "text": "The dark seal on the throne room at the end of the hall cracks and falls away. "
                     "Morvath's voice echoes: 'Come, little hero...'",
             "reward": {"xp": 120, "gold": 60, "items": {"greater_potion": 2}}},
            {"kind": "boss", "target": "lich_king",
             "desc": "Defeat the Lich King Morvath in his throne room.",
             "text": ""},
        ],
        reward={"gold": 500, "xp": 800},
    )
    herbal = Quest(
        "herbal_remedy", "Herbal Remedy", "Sister Elara needs Slime Gel for her fever medicine.",
        giver="elara",
        steps=[{"kind": "collect", "target": "slime_gel", "count": 3, "turn_in": "elara",
                "desc": "Bring 3 Slime Gel to Sister Elara",
                "text": "Oh, thank the light! With this gel the fever tonic will be ready by dusk. "
                        "Please, take these for your trouble.",
                "remind": "I still need the Slime Gel - three pieces. Green slimes in the forest carry it."}],
        reward={"gold": 50, "xp": 60, "items": {"health_potion": 2}},
        offer="The village children are burning with fever. My tonic needs three pieces of Slime Gel - "
              "green slimes in the forest carry it. Could you fetch some?",
        remind="Three pieces of Slime Gel, dear. Green slimes in the forest.",
        thanks="The children are recovering thanks to you. Bless you.",
    )
    pelts = Quest(
        "pelt_collector", "Pelts for Brom", "Brom wants Dire Wolf pelts for winter coats.",
        giver="brom",
        steps=[{"kind": "collect", "target": "wolf_pelt", "count": 3, "turn_in": "brom",
                "desc": "Bring 3 Wolf Pelts to Brom the merchant",
                "text": "Ha! Fine, thick pelts! You've got a merchant's eye, friend. Here - the best "
                        "chainmail my forge ever made. Wear it well!",
                "remind": "Three wolf pelts, friend. The dire wolves in the forest have plenty!"}],
        reward={"gold": 100, "xp": 100, "items": {"chainmail": 1}},
        offer="Winter is coming and my coat orders are piling up. Bring me three Wolf Pelts from the dire "
              "wolves in the forest and I'll make it worth your while!",
        remind="Three wolf pelts. Dire wolves, forest. You know the drill!",
        thanks="Those pelts sold like hot bread. Come back anytime!",
    )
    goblins = Quest(
        "goblin_hunt", "Goblin Menace", "Ranger Lyra wants the goblin raiders thinned out.",
        giver="lyra",
        steps=[
            {"kind": "kill", "target": "goblin", "map": "forest", "count": 4,
             "desc": "Defeat Goblin Raiders in the Whispering Forest",
             "text": ""},
            {"kind": "talk", "target": "lyra",
             "desc": "Report back to Ranger Lyra.",
             "text": "Four fewer knives in the dark. I owe you. Let me teach you a trick - a blade dipped "
                     "in venom. Use it well.",
             "reward": {}},
        ],
        reward={"gold": 80, "xp": 140, "skills": ["venom_strike"]},
        offer="Goblin raiders keep ambushing travelers. Kill four of them and report back. "
              "I'll teach you something useful.",
        remind="Four goblins. They hide in the tall grass. Come back when it's done.",
        thanks="The forest is quieter. Stay sharp, hero.",
    )
    return {q.qid: q for q in (main, herbal, pelts, goblins)}


QUESTS = _build_quests()


def give_reward(player, reward):
    """Hand out gold/xp/items/skills and return reward events."""
    events = []
    if reward.get("gold"):
        player.gold += reward["gold"]
        events.append(("reward", f"  + {gold(reward['gold'])}"))
    if reward.get("xp"):
        events.append(("reward", f"  + {xp(reward['xp'])}"))
        for line in player.gain_xp(reward["xp"]):
            events.append(("reward", line))
    for item_id, qty in reward.get("items", {}).items():
        player.inventory.add(item_id, qty)
        events.append(("reward", f"  + {get_item(item_id).label()} x{qty}"))
    for skill_id in reward.get("skills", []):
        if player.learn_skill(skill_id):
            events.append(("reward", f"  + New skill learned: {SKILL_CLASSES[skill_id].name}!"))
    return events


class QuestLog:
    def __init__(self, state=None):
        # qid -> {"status": "active"|"completed", "step": int, "progress": int}
        self.state = state or {}

    # ---- persistence ---------------------------------------------------------
    def to_dict(self):
        return {qid: dict(s) for qid, s in self.state.items()}

    @classmethod
    def from_dict(cls, data):
        state = {}
        for qid, s in (data or {}).items():
            if qid in QUESTS and s.get("status") in ("active", "completed"):
                state[qid] = {"status": s["status"], "step": int(s.get("step", 0)),
                              "progress": int(s.get("progress", 0))}
        return cls(state)

    # ---- queries -------------------------------------------------------------
    def status(self, qid):
        return self.state.get(qid, {}).get("status")

    def active_ids(self):
        return [q for q, s in self.state.items() if s["status"] == "active"]

    def current_step(self, qid):
        st = self.state[qid]
        return QUESTS[qid].steps[st["step"]]

    def main_stage(self):
        """Index of the current main-quest step (len(steps) once finished)."""
        st = self.state.get(MAIN_QUEST_ID)
        if not st:
            return 0
        return len(QUESTS[MAIN_QUEST_ID].steps) if st["status"] == "completed" else st["step"]

    def objective_text(self, player, qid):
        """Current objective of a quest with live progress numbers."""
        if self.status(qid) != "active":
            return ""
        step, st = self.current_step(qid), self.state[qid]
        if step["kind"] == "kill":
            return f"{step['desc']} ({st['progress']}/{step['count']})"
        if step["kind"] == "collect":
            have = min(player.inventory.count(step["target"]), step["count"])
            return f"{step['desc']} ({have}/{step['count']})"
        return step["desc"]

    # ---- starting & progressing ----------------------------------------------
    def start(self, qid):
        self.state[qid] = {"status": "active", "step": 0, "progress": 0}
        quest = QUESTS[qid]
        return [("quest", f"Quest started: {quest.title}"),
                ("quest", f"Objective: {quest.steps[0]['desc']}")]

    def _finish_step(self, qid, player, spoken=False):
        quest, st = QUESTS[qid], self.state[qid]
        step = quest.steps[st["step"]]
        events = []
        if step.get("text"):
            events.append(("say" if spoken else "story", step["text"]))
        events.append(("quest", f"Objective complete: {step['desc']}"))
        events += give_reward(player, step.get("reward", {}))
        st["step"] += 1
        st["progress"] = 0
        if st["step"] >= len(quest.steps):
            st["status"] = "completed"
            events.append(("quest", f"*** QUEST COMPLETE: {quest.title} ***"))
            events += give_reward(player, quest.reward)
        else:
            events.append(("quest", f"New objective: {quest.steps[st['step']]['desc']}"))
        return events

    def on_talk(self, player, npc_id):
        events = []
        for qid in self.active_ids():
            step = self.current_step(qid)
            if step["kind"] == "talk" and step["target"] == npc_id:
                events += self._finish_step(qid, player, spoken=True)
            elif step["kind"] == "collect" and step["turn_in"] == npc_id:
                if player.inventory.has(step["target"], step["count"]):
                    player.inventory.remove(step["target"], step["count"])
                    events += self._finish_step(qid, player, spoken=True)
                else:
                    events.append(("say", step.get("remind", "You don't have what I asked for yet.")))
        return events

    def _progress(self, player, kind, target_ok):
        events = []
        for qid in self.active_ids():
            step, st = self.current_step(qid), self.state[qid]
            if step["kind"] != kind or not target_ok(step):
                continue
            st["progress"] += 1
            if kind != "kill" or st["progress"] >= step["count"]:
                events += self._finish_step(qid, player)
            else:
                events.append(("quest", f"{QUESTS[qid].title}: {step['desc']} "
                                        f"({st['progress']}/{step['count']})"))
        return events

    def on_kill(self, player, monster, map_id):
        return self._progress(player, "kill", lambda s: (
            s.get("map") in (None, map_id) and s["target"] in ("any", monster.type_id)))

    def on_visit(self, player, map_id):
        return self._progress(player, "visit", lambda s: s["target"] == map_id)

    def on_boss(self, player, monster):
        return self._progress(player, "boss", lambda s: s["target"] == monster.type_id)

    # ---- display -------------------------------------------------------------
    @staticmethod
    def print_events(events, speaker=None):
        for kind, text in events:
            if kind == "say":
                say(speaker, text) if speaker else print(f'"{text}"')
            elif kind == "story":
                narrate(text)
            elif kind == "quest":
                print(quest_text(text))
            else:
                print(text)

    def show(self, player):
        header("Quest Log", C.ORANGE)
        any_active = False
        for qid in self.active_ids():
            quest = QUESTS[qid]
            tag = "MAIN" if quest.is_main else "SIDE"
            print(quest_text(f"[{tag}] {quest.title}"))
            info(f"   {quest.summary}")
            print(f"   > {self.objective_text(player, qid)}")
            any_active = True
        if not any_active:
            info("No active quests.")
        done = [QUESTS[q].title for q, s in self.state.items() if s["status"] == "completed"]
        if done:
            rule()
            print(paint("Completed: ", C.GRAY) + ", ".join(done))
