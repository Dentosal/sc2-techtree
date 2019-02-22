use maplit::hashset;
use std::collections::HashSet;

use sc2_techtree::{TechData, UnitTypeId, UpgradeId};

#[test]
fn upgrade_abilities() {
    let td = TechData::current();

    // Burrow
    assert_eq!(
        td.upgrade_abilities(UpgradeId::new(64))
            .iter()
            .map(|a| a.name.clone())
            .collect::<HashSet<_>>(),
        hashset!["RESEARCH_BURROW".to_owned()]
    );

    // Charge
    assert_eq!(
        td.upgrade_abilities(UpgradeId::new(86))
            .iter()
            .map(|a| a.name.clone())
            .collect::<HashSet<_>>(),
        hashset!["RESEARCH_CHARGE".to_owned()]
    );

    // Invalid upgrade
    assert_eq!(td.upgrade_abilities(UpgradeId::new(123_456)), hashset![]);
}

#[test]
fn morph_abilities() {
    let td = TechData::current();

    // Supplydepot
    assert_eq!(
        td.morph_abilities(UnitTypeId::new(19))
            .iter()
            .map(|a| a.name.clone())
            .collect::<HashSet<_>>(),
        hashset!["MORPH_SUPPLYDEPOT_RAISE".to_owned()]
    );

    // Supplydepotlowered
    assert_eq!(
        td.morph_abilities(UnitTypeId::new(47))
            .iter()
            .map(|a| a.name.clone())
            .collect::<HashSet<_>>(),
        hashset!["MORPH_SUPPLYDEPOT_LOWER".to_owned()]
    );

    // Baneling
    assert_eq!(
        td.morph_abilities(UnitTypeId::new(9))
            .iter()
            .map(|a| a.name.clone())
            .collect::<HashSet<_>>(),
        hashset![
            "MORPHZERGLINGTOBANELING_BANELING".to_owned(),
            "BURROWUP_BANELING".to_owned()
        ]
    );

    // Drone
    assert_eq!(
        td.morph_abilities(UnitTypeId::new(104))
            .iter()
            .map(|a| a.name.clone())
            .collect::<HashSet<_>>(),
        hashset!["LARVATRAIN_DRONE".to_owned(), "BURROWUP_DRONE".to_owned()]
    );
}

#[test]
fn train_abilities() {
    let td = TechData::current();

    // Supplydepots cannot be trained
    assert_eq!(td.train_abilities(UnitTypeId::new(19)), hashset![]);

    // Banelings cannot be trained
    assert_eq!(td.train_abilities(UnitTypeId::new(9)), hashset![]);

    // Drones cannot be trained, they are morphed from larva
    assert_eq!(td.train_abilities(UnitTypeId::new(104)), hashset![]);

    // Invalid units cannot be trained
    assert_eq!(td.train_abilities(UnitTypeId::new(123_456)), hashset![]);

    // Marine
    assert_eq!(
        td.train_abilities(UnitTypeId::new(48))
            .iter()
            .map(|a| a.name.clone())
            .collect::<HashSet<_>>(),
        hashset!["BARRACKSTRAIN_MARINE".to_owned()]
    );

    // Adept
    assert_eq!(
        td.train_abilities(UnitTypeId::new(311))
            .iter()
            .map(|a| a.name.clone())
            .collect::<HashSet<_>>(),
        hashset!["TRAIN_ADEPT".to_owned(), "TRAINWARP_ADEPT".to_owned()]
    );
}

#[test]
fn build_abilities() {
    let td = TechData::current();

    // Banelings cannot be built
    assert_eq!(td.build_abilities(UnitTypeId::new(9)), hashset![]);

    // Drones cannot be built, they are morphed from larva
    assert_eq!(td.build_abilities(UnitTypeId::new(104)), hashset![]);

    // Invalid units cannot be built
    assert_eq!(td.build_abilities(UnitTypeId::new(123_456)), hashset![]);

    // Pylon
    assert_eq!(
        td.build_abilities(UnitTypeId::new(60))
            .iter()
            .map(|a| a.name.clone())
            .collect::<HashSet<_>>(),
        hashset!["PROTOSSBUILD_PYLON".to_owned()]
    );

    // Forge
    assert_eq!(
        td.build_abilities(UnitTypeId::new(63))
            .iter()
            .map(|a| a.name.clone())
            .collect::<HashSet<_>>(),
        hashset!["PROTOSSBUILD_FORGE".to_owned()]
    );

    // Hatchery
    assert_eq!(
        td.build_abilities(UnitTypeId::new(86))
            .iter()
            .map(|a| a.name.clone())
            .collect::<HashSet<_>>(),
        hashset!["ZERGBUILD_HATCHERY".to_owned()]
    );

    // Lair cannot be built, its upgraded from a Hatchery
    assert_eq!(td.build_abilities(UnitTypeId::new(100)), hashset![]);

    // Supplydepot
    assert_eq!(
        td.build_abilities(UnitTypeId::new(19))
            .iter()
            .map(|a| a.name.clone())
            .collect::<HashSet<_>>(),
        hashset!["TERRANBUILD_SUPPLYDEPOT".to_owned()]
    );

    // Supplydepotlowered cannot be built directly
    assert_eq!(td.build_abilities(UnitTypeId::new(47)), hashset![]);
}
