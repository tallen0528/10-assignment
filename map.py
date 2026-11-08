"""map.py - Tile maps: Willowbrook Village, Whispering Forest and the Ashen Crypt.

Legend (inside the layout strings):
    #  wall            T  dense trees (blocked)      ~  deep water (blocked)
    .  safe path       ,  open ground (random encounters happen here in monster zones)
    @  player start    A B E K L  NPCs                1 2  exits to other maps
    X  boss lair       (space) = void, outside the map
"""
from ui import C, paint

WALKABLE = {".", ","}
TILE_NAMES = {"#": "a solid wall", "T": "dense trees", "~": "deep water", " ": "the edge of the world"}

def _build_village():
    """Oval village outline with houses, a pond, a plaza and trees carved in at fixed coordinates."""
    w, h, cx, cy, a, b = 40, 17, 19.5, 8, 18.5, 7.6
    grid = [[" "] * w for _ in range(h)]
    inside = lambda x, y: ((x - cx) / a) ** 2 + ((y - cy) / b) ** 2 <= 1.0
    for y in range(h):
        for x in range(w):
            if inside(x, y):
                grid[y][x] = ","

    def fill(x0, y0, x1, y1, ch):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if 0 <= y < h and 0 <= x < w and grid[y][x] == ",":
                    grid[y][x] = ch

    fill(15, 5, 24, 11, ".")        # central plaza
    fill(2, 8, 37, 8, ".")          # main road west-east
    fill(19, 1, 20, 15, ".")        # road north-south
    fill(6, 2, 10, 4, "#")          # north-west house
    fill(29, 2, 33, 4, "#")         # north-east house
    fill(6, 12, 10, 14, "#")        # south-west house
    fill(29, 12, 33, 14, "#")       # south-east house
    fill(13, 13, 16, 14, "#")       # woodshed
    fill(25, 1, 27, 2, "~")         # small pond ...
    fill(24, 2, 28, 3, "~")
    fill(25, 3, 27, 4, "~")
    for tx, ty in ((3, 5), (3, 6), (4, 5), (34, 10), (35, 10), (34, 11), (13, 2), (14, 2), (22, 14), (23, 14)):
        fill(tx, ty, tx, ty, "T")
    # outline: every empty cell touching the oval becomes a wall
    outline = []
    for y in range(h):
        for x in range(w):
            if grid[y][x] == " " and any(
                    0 <= y + dy < h and 0 <= x + dx < w and grid[y + dy][x + dx] not in (" ", "#")
                    for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                outline.append((x, y))
    for x, y in outline:
        grid[y][x] = "#"
    # NPCs, spawn point and the east gate
    for x, y, ch in ((19, 5, "A"), (24, 9, "B"), (8, 6, "K"), (12, 11, "E"), (5, 8, "@")):
        grid[y][x] = ch
    gate_x = max(x for x in range(w) if grid[8][x] == "#")
    grid[8][gate_x] = "1"
    return ["".join(row).rstrip() for row in grid]


VILLAGE = _build_village()

FOREST = [
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
    "T,,,,,TTTT,,,,,,TTTTT,,,,,,,,TTT,,,,,,,TT   ",
    "T,,,,,,TT,,,,,,,,TTT,,,,,,~~,,,TT,,,,,,,T   ",
    "1.........,,,,,,........,,~~~,,,,,,,,,,,TT  ",
    "TT,,,TTT.TT,,,,,.TTTTT,,,,,~~,,,TTT,,,,,T   ",
    "TTTTTTTT.TTTT,,,.TTTTTTT,,,,,,,,TTTTTTTTTT  ",
    "T,,,,,,,.,,,,,,,.,,,,,,TTTTTTTTTTT,,,,,,TT  ",
    "T,,,,,,,.,TTTT,,.,,,,,,,,,,,,,,,,,,,,,L,TT  ",
    "T,,TTT,,.,TTTT,,.TTTTTTTTTTTTT.TTTTTTTT.TTT  ",
    "T,,TTT,,.,,,,,,,.,,,,,,,,,,,,,.,,,,,,,.,,TT ",
    "TTTTTT,,.TTTTTTTTT,,,TTTTTT,,,,.,TTTTTT.,,,T ",
    "TT,,,,,,..........,,,,,,,,,,,,,,,,,,,,..,,TT",
    "TT,,,TTTTTTTTTTTT,,,,TTTT,,,,~~~,,TTTT,,,,,TT",
    "T,,,,,,,,,,,,,,,,,,,,TTTT,,,,~~~,,TTTT,,,,,T ",
    "T,,TTTT,,,,TTTT,,,,,,,,,,,,,,,,,,,,,,,,,,,,2 ",
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT ",
]

# The crypt is drawn as its left half (centre column last) and mirrored, so it is perfectly symmetric.
_CRYPT_HALF = [
    "             ######",
    "             #,,,,X",
    "             #,,#,,",
    "         #####,,,,,",
    "         #,,,#,,,,,",
    "    ######,,,,#,,,,",
    "    #,,,,,,,,,,,,,,",
    "    #,,##,,,,###,,,",
    "    #,,##,,,,###,,,",
    "    ######,,,,,,,,,",
    "         #,,,,,#,,,",
    "         #####,,,,,",
    "             ####..",
    "               #...",
    "               ###1",
]
CRYPT = ["".join(r.ljust(19) + r.ljust(19)[-2::-1]) for r in _CRYPT_HALF]


class GameMap:
    def __init__(self, map_id, name, rows, intro, npc_chars=None, portals=None, zone=None,
                 encounter_rate=0.0, wall_color=C.GRAY, ground_color=C.GREEN):
        width = max(len(r) for r in rows)
        self.map_id = map_id
        self.name = name
        self.intro = intro
        self.zone = zone                      # key into monster.ZONE_TABLE (None = safe)
        self.encounter_rate = encounter_rate
        self.wall_color = wall_color
        self.ground_color = ground_color
        self.npc_chars = npc_chars or {}      # layout char -> npc id
        self.portals = portals or {}          # layout char -> {"to", "label", ...}
        self.grid = [list(r.ljust(width)) for r in rows]
        self.height, self.width = len(self.grid), width
        self.npc_tiles = {}
        self.portal_tiles = {}
        self.spawn = None
        for y, row in enumerate(self.grid):
            for x, ch in enumerate(row):
                if ch == "@":
                    self.spawn = (x, y)
                    row[x] = "."
                elif ch in self.npc_chars:
                    self.npc_tiles[(x, y)] = self.npc_chars[ch]
                elif ch in self.portals:
                    self.portal_tiles[(x, y)] = ch

    # ---- queries -------------------------------------------------------------
    def tile_at(self, x, y):
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.grid[y][x]
        return " "

    def is_walkable(self, x, y):
        return self.tile_at(x, y) in WALKABLE and (x, y) not in self.npc_tiles

    def is_danger(self, x, y):
        return self.zone is not None and self.tile_at(x, y) == ","

    def npc_at(self, x, y):
        return self.npc_tiles.get((x, y))

    def portal_at(self, x, y):
        key = self.portal_tiles.get((x, y))
        return (key, self.portals[key]) if key else (None, None)

    def describe_tile(self, ch):
        return TILE_NAMES.get(ch, "something in the way")

    def adjacent_npcs(self, x, y):
        found = []
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            npc_id = self.npc_at(x + dx, y + dy)
            if npc_id:
                found.append(npc_id)
        return found

    def arrival_point(self, from_map_id):
        """Walkable tile next to the exit that leads back to `from_map_id`."""
        for (x, y), key in self.portal_tiles.items():
            if self.portals[key]["to"] == from_map_id:
                for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                    if self.is_walkable(x + dx, y + dy):
                        return x + dx, y + dy
        return self.spawn

    # ---- rendering -----------------------------------------------------------
    def _glyph(self, ch, boss_alive):
        if ch == "#":
            return paint("#", self.wall_color)
        if ch == "T":
            return paint("T", C.GREEN, C.BOLD)
        if ch == "~":
            return paint("~", C.BRIGHT_BLUE)
        if ch == ".":
            return paint(".", C.YELLOW, C.DIM)
        if ch == ",":
            return paint(",", self.ground_color)
        if ch == "X":
            return paint("X", C.BRIGHT_RED, C.BOLD) if boss_alive else paint(".", C.YELLOW, C.DIM)
        if ch in self.portals:
            return paint(ch, C.BRIGHT_MAGENTA, C.BOLD)
        if ch in self.npc_chars:
            return paint(ch, C.BRIGHT_BLUE, C.BOLD)
        return ch

    def render(self, px, py, boss_alive=True):
        lines = []
        for y, row in enumerate(self.grid):
            cells = [paint("@", C.BRIGHT_GREEN, C.BOLD) if (x, y) == (px, py)
                     else self._glyph(ch, boss_alive) for x, ch in enumerate(row)]
            lines.append("".join(cells).rstrip())
        return "\n".join(lines)


def build_world():
    return {
        "village": GameMap(
            "village", "Willowbrook Village", VILLAGE,
            "Smoke curls from chimneys as you walk through Willowbrook's cobbled square.",
            npc_chars={"A": "alden", "B": "brom", "E": "elara", "K": "kael"},
            portals={"1": {"to": "forest", "label": "Whispering Forest (east gate)"}},
            wall_color=C.YELLOW, ground_color=C.GREEN),
        "forest": GameMap(
            "forest", "Whispering Forest", FOREST,
            "Twisting roots and restless shadows surround you. Monsters lurk in the tall grass.",
            npc_chars={"L": "lyra"},
            portals={"1": {"to": "village", "label": "Willowbrook Village"},
                     "2": {"to": "crypt", "label": "Ashen Crypt (iron door)", "requires": "crypt_key",
                           "locked": "A huge iron door bars the way. It needs a key - Ranger Lyra may know more."}},
            zone="forest", encounter_rate=0.14, wall_color=C.GRAY, ground_color=C.GREEN),
        "crypt": GameMap(
            "crypt", "Ashen Crypt", CRYPT,
            "Cold air and old dust. Bones crunch underfoot. Something ancient is waiting.",
            portals={"1": {"to": "forest", "label": "Whispering Forest"}},
            zone="crypt", encounter_rate=0.18, wall_color=C.MAGENTA, ground_color=C.GRAY),
    }
