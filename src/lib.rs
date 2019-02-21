//! SC2 Tech Tree
//! A library for validation and querying sc2-techtree data

// Lints
#![warn(clippy::all)]
#![deny(missing_docs)]
#![forbid(unused_must_use)]
// Features
#![feature(type_alias_enum_variants)]

use serde::{Deserialize, Serialize};

mod ability;
mod attribute;
mod cost;
mod ids;
mod race;
mod requirement;
mod unittype;
mod upgrade;
mod weapon;

pub use serde_json::Error as DeserializeError;

pub use self::ability::Ability;
pub use self::attribute::Attribute;
pub use self::cost::Cost;
pub use self::ids::*;
pub use self::race::Race;
pub use self::requirement::Requirement;
pub use self::unittype::UnitType;
pub use self::upgrade::Upgrade;
pub use self::weapon::*;

use self::ability::{AbilityResearch, AbilityTarget};

/// Error when querying tech data
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum QueryError {
    /// Matching item not found
    NotFound,
}

/// All tech data
#[derive(Debug, Serialize, Deserialize, Clone, PartialEq, Eq)]
pub struct TechData {
    /// All abilities
    #[serde(rename = "Ability")]
    pub abilities: Vec<Ability>,
    /// All unit types
    #[serde(rename = "Unit")]
    pub unittypes: Vec<UnitType>,
    /// All upgrades
    #[serde(rename = "Upgrade")]
    pub upgrades: Vec<Upgrade>,
}
impl TechData {
    /// Use the version of the data bundled into this libarary
    pub fn current() -> Self {
        serde_json::from_str::<TechData>(include_str!("../data/data.json")).expect("Invalid bundled data")
    }

    /// Load data from a json string
    pub fn from_json(source: &str) -> Result<Self, DeserializeError> {
        serde_json::from_str::<TechData>(source)
    }

    /// Get an ability by id
    pub fn ability(&self, ability_id: AbilityId) -> Option<Ability> {
        for ability in &self.abilities {
            if ability.id == ability_id {
                return Some(ability.clone());
            }
        }
        None
    }

    /// Get an upgrade by id
    pub fn upgrade(&self, upgrade_id: UpgradeId) -> Option<Upgrade> {
        for upgrade in &self.upgrades {
            if upgrade.id == upgrade_id {
                return Some(upgrade.clone());
            }
        }
        None
    }

    /// Get a unit type by id
    pub fn unittype(&self, unittype_id: UnitTypeId) -> Option<UnitType> {
        for unittype in &self.unittypes {
            if unittype.id == unittype_id {
                return Some(unittype.clone());
            }
        }
        None
    }

    /// Ability that researches an upgrade
    pub fn upgrade_ability(&self, upgrade_id: UpgradeId) -> Result<Ability, QueryError> {
        for ability in &self.abilities {
            if let AbilityTarget::Research(AbilityResearch { upgrade }) = ability.target {
                if upgrade == upgrade_id {
                    return Ok(ability.clone());
                }
            }
        }
        Err(QueryError::NotFound)
    }

    /// Abilities that morph (not train or build) into a unit
    pub fn morph_abilities(&self, unittype_id: UnitTypeId) -> Vec<Ability> {
        let mut result: Vec<Ability> = Vec::new();

        for ability in &self.abilities {
            if let AbilityTarget::Morph(au) = ability.target.clone() {
                if au.produces == unittype_id {
                    result.push(ability.clone());
                }
            } else if let AbilityTarget::MorphPlace(au) = ability.target.clone() {
                if au.produces == unittype_id {
                    result.push(ability.clone());
                }
            }
        }

        result
    }

    /// Abilities that train (not morph or build) a unit
    pub fn train_abilities(&self, unittype_id: UnitTypeId) -> Vec<Ability> {
        let mut result: Vec<Ability> = Vec::new();

        for ability in &self.abilities {
            if let AbilityTarget::Train(au) = ability.target.clone() {
                if au.produces == unittype_id {
                    result.push(ability.clone());
                }
            } else if let AbilityTarget::TrainPlace(au) = ability.target.clone() {
                if au.produces == unittype_id {
                    result.push(ability.clone());
                }
            }
        }

        result
    }
}

#[cfg(test)]
mod tests {
    use super::ids::*;
    use super::{QueryError, TechData};

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
}
