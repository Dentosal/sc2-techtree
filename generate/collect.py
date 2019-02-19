# TODO: Quite flaky

# TODO: buffs, effects
# TODO: zerg morhps, cocoons are bypassed now

from pathlib import Path

import toml

import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.position import Point2
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from s2clientprotocol.data_pb2 import AbilityData, Weapon, Attribute
from s2clientprotocol.raw_pb2 import ActionRaw, ActionRawToggleAutocast


def remove_prefix(s, prefix):
    if s.startswith(prefix):
        return s[len(prefix) :]
    else:
        return s


def remove_postfix(s, postfix):
    if s.endswith(postfix):
        return s[: -len(postfix)]
    else:
        return s


def if_nonzero(v, fn=None):
    if fn:
        return fn(v) if v != 0 else None
    else:
        return v if v != 0 else None


# Specialization
SPEC_PREFIX = ["LIFT_", "LAND_", "BURROWUP_", "BURROWDOWN_"]
SPEC_INFIX = ["ROOT_"]

EMPTY_COST = {"minerals": 0, "gas": 0, "time": 0}


TARGET_DIR = Path("generated") / "collect"
TARGET_DIR.mkdir(exist_ok=True, parents=True)


class MyBot(sc2.BotAI):
    def __init__(self):
        super().__init__()

        self.data_upgrades = []
        self.data_units = []
        self.data_abilities = []

        self.upgrade_abilities = {}
        self.create_abilities = {}

    def serialize_ability(self, a):
        """Return None to skip this."""

        # TODO: Buffs
        # TODO: Check interceptors: BUILD_INTERCEPTORS
        # TODO: Calldowns: SUPPLYDROP_SUPPLYDROP, CALLDOWNMULE_CALLDOWNMULE
        # TODO: Infestors: INFESTEDTERRANS_INFESTEDTERRANS, INFESTORENSNARE_INFESTORENSNARE

        # Unmangled id and name, i.e. unit specific variants also
        real_id = a._proto.ability_id
        real_name = AbilityId(a._proto.ability_id).name

        # Check if useless
        if (
            a.id.name.endswith("_DOORDEFAULTCLOSE")
            or a.id.name.endswith("_BRIDGERETRACT")
            or a.id.name.endswith("_BRIDGEEXTEND")
            or "CRITTER" in real_name
        ):
            return None

        is_morph = (
            "MORPH" in a.id.name
            or a.id.name.startswith("UPGRADETO")
            or a.id.name.startswith("BURROW")
            or a.id.name in ["LIFT", "LAND", "SIEGEMODE_SIEGEMODE", "UNSIEGE_UNSIEGE"]
        )

        is_building = a._proto.is_building or a.id.name == "BUILDAUTOTURRET_AUTOTURRET"

        target_name = AbilityData.Target.Name(a._proto.target)
        if a.id.name in ["BUILD_REACTOR", "BUILD_TECHLAB"]:
            assert target_name == "PointOrNone", f"{a.id.name}: {target_name}"
            if "REACTOR" in a.id.name:
                unit_id = UnitTypeId.REACTOR.value
            elif "TECHLAB" in a.id.name:
                unit_id = UnitTypeId.TECHLAB.value
            else:
                assert False, "Invalid add-on"
            build = {"target": {"BuildInstant": {"produces": unit_id}}}
        elif is_building:
            if real_id in self.create_abilities:
                unit_id = self.create_abilities[real_id]
            else:
                unit_id = 0

            if a._proto.is_instant_placement:
                assert target_name == "PointOrNone", f"{a.id.name}: {target_name}"
                build = {"target": {"BuildInstant": {"produces": unit_id}}}
            elif target_name == "Unit":
                build = {"target": {"BuildOnUnit": {"produces": unit_id}}}
            else:
                assert target_name == "Point", f"{a.id.name}: {target_name}"
                build = {"target": {"Build": {"produces": unit_id}}}
        elif "RESEARCH_" in a.id.name:
            assert target_name == "None", f"{a.id.name}: {target_name}"
            if real_id not in self.upgrade_abilities:
                # Not in the game anymore
                return None

            build = {
                "target": {"Research": {"upgrade": self.upgrade_abilities[real_id]}}
            }
        elif is_morph:
            if real_id in self.create_abilities:
                unit_id = self.create_abilities[real_id]
            else:
                unit_id = 0
                for prefix in SPEC_PREFIX:
                    if real_name.startswith(prefix):
                        name = remove_prefix(real_name, prefix)
                        if name in ["SWARMHOST", "LURKER"]:
                            name += "MP"
                        cands = [
                            u for u in self.data_units if name == u["name"].upper()
                        ]
                        assert len(cands) == 1, name
                        unit_id = cands[0]["id"]
                        break
                for infix in SPEC_INFIX:
                    if infix in real_name:
                        name = real_name[: real_name.find(infix)]
                        cands = [
                            u for u in self.data_units if name == u["name"].upper()
                        ]
                        assert len(cands) == 1, name
                        unit_id = cands[0]["id"]
                        break

            if target_name == "Point":
                build = {"target": {"MorphPlace": {"produces": unit_id}}}
            else:
                assert target_name == "None", f"{a.id.name}: {target_name}"
                build = {"target": {"Morph": {"produces": unit_id}}}
        elif "WARPGATETRAIN_" in a.id.name or "TRAINWARP_ADEPT" == a.id.name:
            assert target_name == "Point", f"{a.id.name}: {target_name}"
            build = {"target": {"TrainPlace": {"produces": 0}}}
        elif "TRAIN_" in a.id.name or a.id.name == "SPAWNCHANGELING_SPAWNCHANGELING":
            assert target_name == "None", f"{a.id.name}: {target_name}"
            build = {"target": {"Train": {"produces": 0}}}
        elif a.id.name.startswith("EFFECT_"):
            # TODO: Effects
            build = {"target": target_name}
        elif a.id.name.startswith("HALLUCINATION_"):
            # TODO: Hallucinations?
            assert target_name == "None", f"{a.id.name}: {target_name}"
            build = {"target": target_name}
        else:
            build = {"target": target_name}

        return {
            **{
                "id": real_id,
                "name": real_name,
                "cast_range": a._proto.cast_range,
                "energy_cost": 0,
                "allow_minimap": a._proto.allow_minimap,
                "allow_autocast": a._proto.allow_autocast,
                "cost": EMPTY_COST,
                "effect": [],
                "buff": [],
                "cooldown": 0,
            },
            **build,
        }

    def serialize_upgrade(self, a):
        return {
            "id": a._proto.upgrade_id,
            "name": a._proto.name,
            "cost": {
                "minerals": a._proto.mineral_cost,
                "gas": a._proto.vespene_cost,
                "time": a._proto.research_time,
            },
        }

    def serialize_buff(self, a):
        return {"id": a._proto.buff_id, "name": a._proto.name}

    def serialize_effect(self, a):
        return {
            "id": a._proto.effect_id,
            "name": a._proto.name,
            "radius": a._proto.radius,
        }

    def serialize_weapon(self, a):
        return {
            "target_type": Weapon.TargetType.Name(a.type),
            "damage_per_hit": a.damage,
            "damage_splash": 0,  # TODO
            "attacks": a.attacks,
            "range": a.range,
            "cooldown": a.speed,
            "bonuses": [
                {"against": Attribute.Name(b.attribute), "damage": b.bonus}
                for b in a.damage_bonus
            ],
        }

    def serialize_unit(self, a):
        if a._proto.food_provided > 0:
            assert a._proto.food_required == 0

        nl = a.name.lower()
        if any(
            w in nl
            for w in [
                "bridge",
                "weapon",
                "missile",
                "preview",
                "dummy",
                "test",
                "alternate",
                "broodlingescort",
            ]
        ):
            return None

        is_structure = Attribute.Value("Structure") in a._proto.attributes

        alias = a._proto.unit_alias
        if alias == 0 and is_structure:
            if a._proto.tech_alias:
                alias = min(a._proto.tech_alias)

        is_worker = a.id in {UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.SCV}
        is_townhall = a.id in {
            UnitTypeId.NEXUS,
            UnitTypeId.COMMANDCENTER,
            UnitTypeId.PLANETARYFORTRESS,
            UnitTypeId.ORBITALCOMMAND,
            UnitTypeId.HATCHERY,
            UnitTypeId.LAIR,
            UnitTypeId.HIVE,
        }
        is_addon = a.id in {
            UnitTypeId.REACTOR,
            UnitTypeId.BARRACKSREACTOR,
            UnitTypeId.FACTORYREACTOR,
            UnitTypeId.STARPORTREACTOR,
            UnitTypeId.TECHLAB,
            UnitTypeId.BARRACKSTECHLAB,
            UnitTypeId.FACTORYTECHLAB,
            UnitTypeId.STARPORTTECHLAB,
        }

        needs_gayser = a.id in {
            UnitTypeId.ASSIMILATOR,
            UnitTypeId.REFINERY,
            UnitTypeId.EXTRACTOR,
            UnitTypeId.ASSIMILATORRICH,
            UnitTypeId.REFINERYRICH,
            UnitTypeId.EXTRACTORRICH,
        }
        needs_power = a.id in {
            UnitTypeId.GATEWAY,
            UnitTypeId.FORGE,
            UnitTypeId.CYBERNETICSCORE,
            UnitTypeId.WARPGATE,
            UnitTypeId.PHOTONCANNON,
            UnitTypeId.SHIELDBATTERY,
            UnitTypeId.ROBOTICSFACILITY,
            UnitTypeId.ROBOTICSBAY,
            UnitTypeId.STARGATE,
            UnitTypeId.FLEETBEACON,
            UnitTypeId.TEMPLARARCHIVE,
            UnitTypeId.DARKSHRINE,
        }
        needs_creep = (
            a.race == Race.Zerg
            and is_structure
            and a.id
            not in {
                UnitTypeId.HATCHERY,
                UnitTypeId.LAIR,
                UnitTypeId.HIVE,
                UnitTypeId.EXTRACTOR,
                UnitTypeId.EXTRACTORRICH,
            }
        )
        accepts_addon = a.id in {
            UnitTypeId.BARRACKS,
            UnitTypeId.FACTORY,
            UnitTypeId.STARPORT,
        }

        return {
            "id": a.id.value,
            "name": a.name,
            "normal_mode": alias if alias != 0 else None,
            "race": a.race.name,
            "supply": a._proto.food_required - a._proto.food_provided,
            "cargo_size": if_nonzero(a._proto.cargo_size),
            "cargo_capacity": None,  # Use created unit to check
            "max_health": {"hp": 0, "shield": None},  # Use created unit to check
            "armor": a._proto.armor,
            "sight": a._proto.sight_range,
            "detection_range": None,  # Use created unit to check
            "speed": if_nonzero(a._proto.movement_speed),
            "speed_creep_mul": 1.0,
            "max_energy": None,  # Use created unit to check
            "start_energy": None,  # Use created unit to check
            "weapons": [self.serialize_weapon(w) for w in a._proto.weapons],
            "attributes": [Attribute.Name(a) for a in a._proto.attributes],
            "abilities": [],  # Use created unit to check
            "size": 0,  # Use created unit to check
            "radius": 0,  # Use created unit to check
            "power_radius": None,  # Use created unit to check
            "accepts_addon": accepts_addon,
            "needs_power": needs_power,
            "needs_creep": needs_creep,
            "needs_gayser": needs_gayser,
            "is_structure": is_structure,
            "is_addon": is_addon,
            "is_worker": is_worker,
            "is_townhall": is_townhall,
        }

    def on_start(self):
        for id, a in self._game_data.upgrades.items():
            if a._proto.name != "" and a._proto.HasField("research_time"):
                self.data_upgrades.append(self.serialize_upgrade(a))
                self.upgrade_abilities[a._proto.ability_id] = a._proto.upgrade_id

        for id, a in self._game_data.units.items():
            assert a._proto.name != ""
            if a.race != Race.NoRace:
                u = self.serialize_unit(a)
                if u is not None:
                    self.data_units.append(u)
                    self.create_abilities[a._proto.ability_id] = a._proto.unit_id

        for id, a in self._game_data.abilities.items():
            abl = self.serialize_ability(a)
            if abl is not None:
                self.data_abilities.append(abl)

        self.unit_queue = [u["id"] for u in self.data_units[::-1]]
        self.current_unit = None
        self.wait_steps = 0
        self.__state = "Empty"

    def recognizes_ability(self, a_id):
        """Has this ability been added?"""
        assert isinstance(a_id, int)
        return a_id in [int(a["id"]) for a in self.data_abilities]

    def is_specialization(self, abil_name):
        """Is this ability use this a specialization, e.g. LIFT_COMMANDCENTER instead of LIFT."""
        assert isinstance(abil_name, str)
        assert abil_name == abil_name.upper()

        for prefix in SPEC_PREFIX:
            if abil_name.startswith(prefix):
                return True
        for infix in SPEC_INFIX:
            if infix in abil_name:
                return True

        return False

    def ability_specialization_allowed_for(self, a_id, u_id):
        """Can this unit use this specialization, e.g. do not allow LIFT_COMMANDCENTER for BARRACKS."""
        assert isinstance(a_id, int)
        assert isinstance(u_id, int)

        a_name = AbilityId(a_id).name.upper()
        u_name = UnitTypeId(u_id).name

        if not self.is_specialization(a_name):
            return True

        for postfix in ["FLYING", "BURROWED", "MP"]:
            u_name = remove_postfix(u_name, postfix)

        return u_name in a_name

    async def state_step(self):
        self.wait_steps -= 1
        if self.wait_steps > 0:
            return

        if self.__state == "Empty":
            if len(self.unit_queue) == 0:
                with (TARGET_DIR / "upgrade.toml").open("w") as f:
                    f.write(toml.dumps({"Upgrade": self.data_upgrades}))

                with (TARGET_DIR / "unit.toml").open("w") as f:
                    f.write(toml.dumps({"Unit": self.data_units}))

                with (TARGET_DIR / "ability.toml").open("w") as f:
                    f.write(toml.dumps({"Ability": self.data_abilities}))

                await self._client.leave()
                return

            print("Units left:", len(self.unit_queue))
            self.current_unit = self.unit_queue.pop()
            await self._client.debug_create_unit(
                [[UnitTypeId(self.current_unit), 1, self._game_info.map_center, 1]]
            )

            self.time_left = 10
            self.__state = "WaitCreate"

        elif self.__state == "WaitCreate":
            if len(self.units) == 0 and self.current_unit == UnitTypeId.LARVA.value:
                # Larva cannot be created without a hatchery
                await self._client.debug_create_unit(
                    [[UnitTypeId.HATCHERY, 1, self._game_info.map_center, 1]]
                )
                self.wait_steps = 10
                return
            elif len(self.units) == 0:
                self.time_left -= 1
                if self.time_left < 0:
                    index = [
                        i
                        for i, u in enumerate(self.data_units)
                        if u["id"] == self.current_unit
                    ][0]
                    del self.data_units[index]
                    self.__state = "Clear"
            else:
                cands = [
                    u for u in self.units if u._proto.unit_type == self.current_unit
                ]
                if len(cands) == 0:
                    # Check for some allowed specialization
                    su = self.units.first.name.upper()
                    lu = UnitTypeId(self.current_unit).name.upper()
                    if len(self.units) == 1 and (
                        su in lu or all(n.startswith("CREEPTUMOR") for n in (su, lu))
                    ):
                        unit = self.units.first
                    else:
                        assert (
                            False
                        ), f"Invalid self.units (looking for {UnitTypeId(self.current_unit) !r}): {self.units}"
                else:
                    unit = cands[0]
                assert unit.is_ready
                index = [
                    i
                    for i, u in enumerate(self.data_units)
                    if u["id"] == self.current_unit
                ][0]

                if self.current_unit in [
                    UnitTypeId.CREEPTUMOR.value,
                    UnitTypeId.CREEPTUMORQUEEN.value,
                ]:
                    # TODO: Handle this properly
                    # Creep tumors automatically burrow when complete
                    # CREEPTUMORBURROWED
                    pass
                elif self.current_unit == UnitTypeId.LARVA.value:
                    # Larva must be selected
                    unit = self.units(UnitTypeId.LARVA).first
                elif self.current_unit in [
                    UnitTypeId.BARRACKSTECHLAB.value,
                    UnitTypeId.BARRACKSREACTOR.value,
                    UnitTypeId.FACTORYTECHLAB.value,
                    UnitTypeId.FACTORYREACTOR.value,
                    UnitTypeId.STARPORTTECHLAB.value,
                    UnitTypeId.STARPORTREACTOR.value,
                ]:
                    # Reactors and tech labs are not really part of the building,
                    # so to get the abilities an appropriate building must be added.
                    # Bare Reactor and TechLab have no abilities, so not matching them here.
                    if self.current_unit in [
                        UnitTypeId.BARRACKSTECHLAB.value,
                        UnitTypeId.BARRACKSREACTOR.value,
                    ]:
                        ut = UnitTypeId.BARRACKS
                    elif self.current_unit in [
                        UnitTypeId.FACTORYTECHLAB.value,
                        UnitTypeId.FACTORYREACTOR.value,
                    ]:
                        ut = UnitTypeId.FACTORY
                    elif self.current_unit in [
                        UnitTypeId.STARPORTTECHLAB.value,
                        UnitTypeId.STARPORTREACTOR.value,
                    ]:
                        ut = UnitTypeId.STARPORT
                    else:
                        assert False, f"Type? {unit.type_id.name}"

                    if len(self.units) > 1:
                        assert len(self.units) == 2 and all(
                            u.is_ready for u in self.units
                        )
                        # Building and addon both created
                    else:
                        await self._client.debug_create_unit(
                            [[ut, 1, self._game_info.map_center, 1]]
                        )
                        await self._client.debug_kill_unit([unit.tag])
                        self.wait_steps = 100
                        self.__state = "BuildAddOn"
                        return
                elif self.data_units[index]["needs_power"]:
                    # Build pylon for protoss buildings that need it

                    if len(self.units) > 1:
                        assert len(self.units) == 2, f"Units: {self.units}"
                        assert all(u.is_ready for u in self.units)
                        assert len(self.state.psionic_matrix.sources) == 1
                        # Pylon already created
                    else:
                        if self.current_unit == UnitTypeId.GATEWAY.value:
                            # Disable autocast of warpgate morph
                            await self._client.toggle_autocast(
                                [unit], AbilityId.MORPH_WARPGATE
                            )

                        await self._client.debug_create_unit(
                            [[UnitTypeId.PYLON, 1, self._game_info.map_center, 1]]
                        )

                        self.wait_steps = 200
                        return
                else:
                    assert (
                        self.current_unit == unit.type_id.value
                    ), f"{self.current_unit} == {unit.type_id.value} ({unit.type_id})"

                self.data_units[index]["cargo_capacity"] = if_nonzero(
                    unit._proto.cargo_space_max
                )
                self.data_units[index]["max_health"] = unit._proto.health_max
                self.data_units[index]["max_shield"] = if_nonzero(
                    unit._proto.shield_max
                )
                self.data_units[index]["detection_range"] = if_nonzero(
                    unit._proto.detect_range
                )
                self.data_units[index]["start_energy"] = if_nonzero(
                    unit._proto.energy, int
                )
                self.data_units[index]["max_energy"] = if_nonzero(
                    unit._proto.energy_max
                )
                self.data_units[index]["radius"] = if_nonzero(unit._proto.radius)
                # TODO: "placement_size" for buildings

                # Provided power radius
                power_sources = self.state.psionic_matrix.sources
                if len(power_sources) > 0:
                    assert len(power_sources) == 1
                    self.data_units[index]["power_radius"] = power_sources[0].radius

                # Unit abilities
                try:
                    abilities = (
                        await self.get_available_abilities(
                            [unit], ignore_resource_requirements=True
                        )
                    )[0]

                    # No requirements when all tech is locked
                    self.data_units[index]["abilities"] = [
                        {"ability": a.value}
                        for a in abilities
                        if self.recognizes_ability(a.value)
                        and self.ability_specialization_allowed_for(
                            a.value, unit._proto.unit_type
                        )
                    ]

                    # See requirement-depending upgrades with tech
                    await self._client.debug_tech_tree()
                    self.__state = "TechCheck"

                except ValueError as e:
                    assert "is not a valid AbilityId" in repr(e), repr(e)
                    # TODO: maybe skip the unit entirely
                    self.__state = "Clear"

        elif self.__state == "BuildAddOn":
            assert len(self.units) == 1, f"? {self.units}"
            unit = self.units.first
            await self.do(unit.build(UnitTypeId(self.current_unit)))
            self.wait_steps = 10
            self.__state = "BuildAddOnWait"

        elif self.__state == "BuildAddOnWait":
            assert len(self.units) == 2, f"? {self.units}"
            if all(u.is_ready for u in self.units):
                self.__state = "WaitCreate"

        elif self.__state == "TechCheck":
            possible_units = [
                u for u in self.units if u._proto.unit_type == self.current_unit
            ]
            if possible_units:
                unit = possible_units[0]
                assert unit.is_ready
                index = [
                    i
                    for i, u in enumerate(self.data_units)
                    if u["id"] == self.current_unit
                ][0]

                abilities = (
                    await self.get_available_abilities(
                        [unit], ignore_resource_requirements=True
                    )
                )[0]

                print("#", unit)
                for a in abilities:
                    print(">", a)
                    if not self.recognizes_ability(a.value):
                        continue

                    if not self.ability_specialization_allowed_for(
                        a.value, unit._proto.unit_type
                    ):
                        continue

                    if a.value not in [
                        a["ability"] for a in self.data_units[index]["abilities"]
                    ]:
                        self.data_units[index]["abilities"].append(
                            {"requirements": "???", "ability": a.value}
                        )

            # Switch all tech back off
            await self._client.debug_tech_tree()
            self.__state = "Clear"

        elif self.__state == "WaitCreate":
            if len(self.units) == 0:
                self.time_left -= 1
                if self.time_left < 0:
                    self.__state = "Clear"

        elif self.__state == "WaitEmpty":
            if len(self.units) > 0:
                self.time_left -= 1
                if self.time_left < 0:
                    assert False, "Clear failed"
                else:
                    # Kill broodlings etc
                    for u in self.state.units:
                        await self._client.debug_kill_unit([u.tag])
                        self.wait_steps = 20
            else:
                self.__state = "Empty"

        if self.__state == "Clear":
            for u in self.state.units:
                await self._client.debug_kill_unit([u.tag])
                self.wait_steps = 20

            self.current_unit = None
            self.__state = "WaitEmpty"
            self.time_left = 10

    async def on_step(self, iteration):
        for unit in self.units:
            self._client.debug_text_world(
                f"{unit.type_id.name}:{unit.type_id.value}\n({unit.position})",
                unit.position3d,
                color=(0, 255, 0),
                size=12,
            )

        await self._client.send_debug()

        # Create all units (including structures) to get more info
        if iteration == 0:
            await self._client.debug_fast_build()  # Must build addons
            await self._client.debug_cooldown()
            await self._client.debug_all_resources()  # Must build addons
            await self._client.debug_god()  # Larva must not die
        else:
            await self.state_step()


def collect():
    run_game(maps.get("Empty128"), [Bot(Race.Zerg, MyBot())], realtime=False)


if __name__ == "__main__":
    collect()
