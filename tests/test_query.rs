use sc2_techtree::{QueryError, TechData, UnitTypeId, UpgradeId};

use std::fs::File;
use std::io::prelude::*;

#[test]
fn load_data() {
    let mut f = File::open("data/data.json").expect("File not found");

    let mut contents = String::new();
    f.read_to_string(&mut contents).expect("Could not read");

    TechData::from_json(&contents).expect("Deserialization failed");
}

#[test]
fn upgrade_ability() {
    let td = TechData::current();

    // Burrow
    assert_eq!(
        td.upgrade_ability(UpgradeId::new(64)).unwrap().name,
        "RESEARCH_BURROW"
    );

    // Charge
    assert_eq!(
        td.upgrade_ability(UpgradeId::new(86)).unwrap().name,
        "RESEARCH_CHARGE"
    );

    // Invalid upgrade
    assert_eq!(
        td.upgrade_ability(UpgradeId::new(123_456)),
        Err(QueryError::NotFound)
    );
}

#[test]
fn morph_abilities() {
    let td = TechData::current();

    // Supplydepot
    assert_eq!(
        td.morph_abilities(UnitTypeId::new(19))
            .iter()
            .map(|a| a.name.clone())
            .collect::<Vec<_>>(),
        vec!["MORPH_SUPPLYDEPOT_RAISE"]
    );

    // Supplydepotlowered
    assert_eq!(
        td.morph_abilities(UnitTypeId::new(47))
            .iter()
            .map(|a| a.name.clone())
            .collect::<Vec<_>>(),
        vec!["MORPH_SUPPLYDEPOT_LOWER"]
    );

    // Baneling
    assert_eq!(
        td.morph_abilities(UnitTypeId::new(9))
            .iter()
            .map(|a| a.name.clone())
            .collect::<Vec<_>>(),
        vec!["MORPHZERGLINGTOBANELING_BANELING", "BURROWUP_BANELING"]
    );

    // Drone
    assert_eq!(
        td.morph_abilities(UnitTypeId::new(104))
            .iter()
            .map(|a| a.name.clone())
            .collect::<Vec<_>>(),
        vec!["LARVATRAIN_DRONE", "BURROWUP_DRONE"]
    );
}

#[test]
fn train_abilities() {
    let td = TechData::current();

    // Supplydepots cannot be trained
    assert_eq!(td.train_abilities(UnitTypeId::new(19)), vec![]);

    // Banelings cannot be trained
    assert_eq!(td.train_abilities(UnitTypeId::new(9)), vec![]);

    // Drones cannot be trained, they are morphed from larva
    assert_eq!(td.train_abilities(UnitTypeId::new(104)), vec![]);

    // Invalid units cannot be trained
    assert_eq!(td.train_abilities(UnitTypeId::new(123_456)), vec![]);

    // Marine
    assert_eq!(
        td.train_abilities(UnitTypeId::new(48))
            .iter()
            .map(|a| a.name.clone())
            .collect::<Vec<_>>(),
        vec!["BARRACKSTRAIN_MARINE"]
    );

    // Adept
    assert_eq!(
        td.train_abilities(UnitTypeId::new(311))
            .iter()
            .map(|a| a.name.clone())
            .collect::<Vec<_>>(),
        vec!["TRAIN_ADEPT", "TRAINWARP_ADEPT"]
    );
}

#[test]
fn build_abilities() {
    let td = TechData::current();

    // Banelings cannot be built
    assert_eq!(td.build_abilities(UnitTypeId::new(9)), vec![]);

    // Drones cannot be built, they are morphed from larva
    assert_eq!(td.build_abilities(UnitTypeId::new(104)), vec![]);

    // Invalid units cannot be built
    assert_eq!(td.build_abilities(UnitTypeId::new(123_456)), vec![]);

    // Pylon
    assert_eq!(
        td.build_abilities(UnitTypeId::new(60))
            .iter()
            .map(|a| a.name.clone())
            .collect::<Vec<_>>(),
        vec!["PROTOSSBUILD_PYLON"]
    );

    // Forge
    assert_eq!(
        td.build_abilities(UnitTypeId::new(63))
            .iter()
            .map(|a| a.name.clone())
            .collect::<Vec<_>>(),
        vec!["PROTOSSBUILD_FORGE"]
    );

    // Hatchery
    assert_eq!(
        td.build_abilities(UnitTypeId::new(86))
            .iter()
            .map(|a| a.name.clone())
            .collect::<Vec<_>>(),
        vec!["ZERGBUILD_HATCHERY"]
    );

    // Lair cannot be built, its upgraded from a Hatchery
    assert_eq!(td.build_abilities(UnitTypeId::new(100)), vec![]);

    // Supplydepot
    assert_eq!(
        td.build_abilities(UnitTypeId::new(19))
            .iter()
            .map(|a| a.name.clone())
            .collect::<Vec<_>>(),
        vec!["TERRANBUILD_SUPPLYDEPOT"]
    );

    // Supplydepotlowered cannot be built directly
    assert_eq!(td.build_abilities(UnitTypeId::new(47)), vec![]);
}
