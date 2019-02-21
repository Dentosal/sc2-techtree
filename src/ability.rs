use noisy_float::prelude::*;
use serde::{Deserialize, Serialize};

use crate::cost::Cost;
use crate::ids::*;

/// Ability
#[derive(Debug, Serialize, Deserialize, Clone, PartialEq, Eq)]
pub struct Ability {
    /// Id
    pub id: AbilityId,
    /// Name
    pub name: String,
    /// Target type and data
    pub target: AbilityTarget,
    /// Cast range
    pub cast_range: Option<R32>,
    /// Energy cost
    pub energy_cost: Option<u32>,
    /// Monetary / time cost
    pub cost: Cost,
    /// Effects
    pub effect: Vec<()>, // TODO
    /// Buffs
    pub buff: Vec<()>, // TODO
    /// Cooldown
    pub cooldown: Option<R32>,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq, Eq)]
pub enum AbilityTarget {
    None,
    Point,
    Unit,
    PointOrUnit,
    PointOrNone,
    /// Self-mutating morphs
    Morph(AbilityUnit),
    /// Self-mutating morphs locking to specific position
    MorphPlace(AbilityUnit),
    /// Unit training
    Train(AbilityUnit),
    /// Protoss warp-ins
    TrainPlace(AbilityUnit),
    /// Normal structures
    Build(AbilityUnit),
    /// Vespene gaysers
    BuildOnUnit(AbilityUnit),
    /// Add-ons
    BuildInstant(AbilityUnit),
    /// Research
    Research(AbilityResearch),
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq, Eq)]
pub struct AbilityUnit {
    /// Produced unit
    pub produces: UnitTypeId,
    /// Zerglings are created in pairs, false for everything else
    #[serde(default)]
    pub double: bool,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq, Eq)]
pub struct AbilityResearch {
    /// Upgrades
    pub upgrade: UpgradeId,
}
