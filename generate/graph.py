from __future__ import annotations

import typing as ty

from pathlib import Path
from copy import deepcopy

import json

TARGET_DIR = Path("generated") / "results"
GV_DOT_DIR = Path("generated") / "visuals"


COMMON_ABILS = [
    "SMART",
    "MOVE",
    "PATROL",
    "HOLDPOSITION",
    "STOP_STOP",
    "ATTACK_ATTACK",
    "SCAN_MOVE",
    "RALLY_BUILDING",
]


class Vertex:
    def __init__(self, vtype, value):
        assert isinstance(vtype, str), vtype
        assert isinstance(value, dict), value
        assert "name" in value

        self.vtype = vtype
        self.value = value

    def __repr__(self):
        return f"({self.value['name']}: {self.vtype})"

    def __eq__(self, other):
        if self.vtype != other.vtype:
            return False

        return self.value["name"] == other.value["name"]

    def __hash__(self):
        return hash(repr(self))


class Edge:
    def __init__(self, start_type, end_type, start, end, **kwargs):
        self.start_type = start_type
        self.end_type = end_type
        self.start = start
        self.end = end
        self.kwargs = kwargs

    def __eq__(self, other):
        return self.startv == other.startv and self.endv == other.endv

    @property
    def startv(self) -> Vertex:
        return Vertex(self.start_type, self.start)

    @property
    def endv(self) -> Vertex:
        return Vertex(self.end_type, self.end)

    @property
    def as_viz(self):
        # viz = f"{self.start['name']}_{self.start['id']} -> {self.end['name']}_{self.end['id']}"
        viz = f"{self.start['name']} -> {self.end['name']}"
        attrs = [f"{k}={v}" for k, v in self.kwargs.items()]
        if attrs:
            viz += f"[{','.join(attrs)}]"
        return viz + ";"


class Graph:
    def __init__(self):
        self.edges = []
        self.vizcfg = set()

    def add(self, edge: Edge):
        if edge not in self.edges:
            self.edges.append(edge)

    def edges_from_vertex(self, v: Vertex) -> ty.Iterable[Vertex]:
        for edge in self.edges:
            if edge.startv == v:
                yield edge

    def filter_disconnected(self, pin: Vertex) -> Graph:
        connected = {pin}
        queue = [pin]

        while queue:
            v = queue.pop()
            for edge in self.edges_from_vertex(v):
                if edge.endv not in connected and edge.endv not in queue:
                    connected.add(edge.endv)
                    queue.append(edge.endv)

        g = deepcopy(self)
        g.edges = [e for e in g.edges if e.endv in connected and e.startv in connected]
        return g

    def filter(
        self, skip_common=False, skip_extra=False, skip_upgrades=False, limit_race=None
    ) -> Graph:
        def incl_unit(unit):
            if skip_extra and unit["name"].endswith("Flying"):
                return False
            return (not limit_race) or unit["race"] == limit_race

        def incl_abil(abil):
            if skip_extra and (
                any(
                    abil["name"].startswith(p)
                    for p in ["HALLUCINATION_", "LIFT_", "LAND_", "LOAD_"]
                )
                or any(abil["name"].endswith(p) for p in ["LEVEL1", "LEVEL2", "LEVEL3"])
            ):
                return False
            return (not skip_common) or abil["name"] not in COMMON_ABILS

        def keep(e: Edge) -> bool:
            if e.start_type == "Ability" and not incl_abil(e.start):
                return False
            if e.end_type == "Ability" and not incl_abil(e.end):
                return False
            if e.start_type == "Unit" and not incl_unit(e.start):
                return False
            if e.end_type == "Unit" and not incl_unit(e.end):
                return False
            if skip_upgrades and (e.start_type == "Upgrade" or e.end_type == "Upgrade"):
                return False
            return True

        g = deepcopy(self)

        if limit_race:
            if limit_race == "Protoss":
                g = g.filter_disconnected(Vertex("Unit", {"name": "Probe"}))
            elif limit_race == "Zerg":
                g = g.filter_disconnected(Vertex("Unit", {"name": "Larva"}))
            elif limit_race == "Terran":
                g = g.filter_disconnected(Vertex("Unit", {"name": "SCV"}))
            else:
                assert False, f"Invalid race limit {limit_race}"

        g.edges = [e for e in g.edges if keep(e)]

        if (not limit_race) or limit_race == "Protoss":
            g.vizcfg.add("{rank=same Gateway WarpGate}")
        elif (not limit_race) or limit_race == "Zerg":
            g.vizcfg.add("{rank=same Lair Queen}")
        return g

    def viz(self) -> str:
        lines = []

        lines.append("digraph A {")
        lines.append("node [shape=record];")
        lines.append("graph [pad=0.5, nodesep=0.2, ranksep=0.8];")
        lines.append("rankdir=LR;")

        for edge in self.edges:
            lines.append(edge.as_viz)

        for cfg in self.vizcfg:
            lines.append(cfg)

        lines.append("}")

        return "\n".join(lines)

    @classmethod
    def build(cls, c_ability, c_unit, c_upgrade, requirements=False):
        self = cls()

        for unit in c_unit["Unit"]:
            for unit_a in unit["abilities"]:
                ua = unit_a["ability"]
                ra_cands = [a for a in c_ability["Ability"] if int(a["id"]) == ua]
                assert (
                    len(ra_cands) == 1
                ), f"Multiple or zero matching abilities for {ua}: {ra_cands}"
                ra = ra_cands[0]

                self.add(Edge("Unit", "Ability", unit, ra))

                if requirements:
                    rq = unit_a.get("requirements")
                    if rq is not None:
                        for r in rq:
                            assert len(r.keys()) == 1
                            k = list(r.keys())[0]
                            if k == "upgrade":
                                up = [
                                    u
                                    for u in c_upgrade["Upgrade"]
                                    if int(u["id"]) == r[k]
                                ][0]
                                self.add(
                                    Edge(
                                        "Ability",
                                        "Upgrade",
                                        ra,
                                        up,
                                        style="dashed",
                                        dir="back",
                                    )
                                )
                            elif k == "building":
                                un = [
                                    u for u in c_unit["Unit"] if int(u["id"]) == r[k]
                                ][0]
                                self.add(
                                    Edge(
                                        "Ability",
                                        "Unit",
                                        ra,
                                        un,
                                        style="dashed",
                                        dir="back",
                                    )
                                )
                            elif k in ["addon", "addon_to"]:
                                un = [
                                    u for u in c_unit["Unit"] if int(u["id"]) == r[k]
                                ][0]
                                self.add(
                                    Edge(
                                        "Ability",
                                        "Unit",
                                        ra,
                                        un,
                                        style="dashed",
                                        dir="back",
                                    )
                                )
                            else:
                                assert False, f"Unknown requirement type: {k}"

        for abil in c_ability["Ability"]:
            target = abil.get("target")
            if target is not None and isinstance(target, dict):
                keys = target.keys()
                assert len(keys) == 1
                k = list(keys)[0]

                if k == "Research":
                    tg = target[k]["upgrade"]
                    up = [u for u in c_upgrade["Upgrade"] if int(u["id"]) == tg]
                    self.add(Edge("Ability", "Upgrade", abil, up[0]))
                else:
                    tg = target[k]["produces"]
                    un = [u for u in c_unit["Unit"] if int(u["id"]) == tg]
                    if un != []:
                        self.add(Edge("Ability", "Unit", abil, un[0]))

        return self


def graph():
    GV_DOT_DIR.mkdir(exist_ok=True)

    with (TARGET_DIR / "ability.json").open() as f:
        c_ability = json.load(f)

    with (TARGET_DIR / "unit.json").open() as f:
        c_unit = json.load(f)

    with (TARGET_DIR / "upgrade.json").open() as f:
        c_upgrade = json.load(f)

    for race in ["Protoss", "Zerg", "Terran"]:
        for requirements in [True, False]:
            g = (
                Graph.build(c_ability, c_unit, c_upgrade, requirements=requirements)
                .filter(
                    skip_common=True,
                    skip_extra=False,
                    skip_upgrades=False,
                    limit_race=race,
                )
                .viz()
            )

            key = ["techtree", race.lower()]
            if not requirements:
                key.append("noreqs")
            with (GV_DOT_DIR / ("_".join(key) + ".dot")).open("w") as f:
                f.write(g + "\n")


if __name__ == "__main__":
    graph()
