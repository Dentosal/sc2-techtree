//! Terminology:
//! Attack = Single projectile or strike
//! Hit = Attack that connects with the target

use noisy_float::prelude::*;
use serde::{Deserialize, Serialize};

use super::attribute::Attribute;

/// Weapon target type
#[derive(Debug, Serialize, Deserialize, Clone, PartialEq, Eq)]
pub enum WeaponTargetType {
    /// To ground only
    Ground,
    /// To air only
    Air,
    /// To ground and air both
    Any,
}

/// Weapon bonus
#[derive(Debug, Serialize, Deserialize, Clone, PartialEq, Eq)]
pub struct WeaponBonus {
    /// Bonus affects attacks against units having this attribute
    against: Attribute,
    /// The amount of bonus damage per hit
    damage: R32,
}

/// Weapon
#[derive(Debug, Serialize, Deserialize, Clone, PartialEq, Eq)]
pub struct Weapon {
    target_type: WeaponTargetType,
    /// Damage per hit, no upgrades
    damage_per_hit: R32,
    /// Percentage
    damage_splash: R32,
    /// Attacks per one attack tick, e.g. 2 for Colossus
    attacks: u32,
    /// Range
    range: R32,
    /// Cooldown
    cooldown: R32,
    /// Bonuses
    bonuses: Vec<WeaponBonus>,
}
