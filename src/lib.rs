//! SC2 Tech Tree
//! A library for validation and querying sc2-techtree data

// Lints
#![warn(clippy::all)]
#![deny(missing_docs)]
#![forbid(unused_must_use)]
// Features
#![feature(type_alias_enum_variants)]
#![feature(bind_by_move_pattern_guards)]

use std::collections::HashSet;

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

    /// Abilities with matching target
    pub fn abilities_by_target<F>(&self, f: F) -> HashSet<Ability>
    where
        F: Fn(AbilityTarget) -> bool,
    {
        self.abilities
            .iter()
            .filter(|a| f(a.target.clone()))
            .cloned()
            .collect()
    }

    /// Abilities that research an upgrade
    pub fn upgrade_abilities(&self, upgrade_id: UpgradeId) -> HashSet<Ability> {
        self.abilities_by_target(|target| {
            AbilityTarget::Research(AbilityResearch { upgrade: upgrade_id }) == target
        })
    }

    /// Abilities that morph (not train or build) into a unit
    pub fn morph_abilities(&self, unittype_id: UnitTypeId) -> HashSet<Ability> {
        self.abilities_by_target(|target| {
            if let AbilityTarget::Morph(au) = target {
                au.produces == unittype_id
            } else if let AbilityTarget::MorphPlace(au) = target {
                au.produces == unittype_id
            } else {
                false
            }
        })
    }

    /// Abilities that train (not morph or build) a unit
    pub fn train_abilities(&self, unittype_id: UnitTypeId) -> HashSet<Ability> {
        self.abilities_by_target(|target| {
            if let AbilityTarget::Train(au) = target {
                au.produces == unittype_id
            } else if let AbilityTarget::TrainPlace(au) = target {
                au.produces == unittype_id
            } else {
                false
            }
        })
    }

    /// Abilities that build (not morph or train) a (structure) unit
    /// This includes Drone "morphs" to structures
    pub fn build_abilities(&self, unittype_id: UnitTypeId) -> HashSet<Ability> {
        self.abilities_by_target(|target| {
            if let AbilityTarget::Build(au) = target {
                au.produces == unittype_id
            } else {
                false
            }
        })
    }
}
