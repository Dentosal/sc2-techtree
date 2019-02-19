use serde::{Deserialize, Serialize};

/// Unit type
#[derive(Debug, Serialize, Deserialize, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct UnitTypeId(u32);

/// Ability
#[derive(Debug, Serialize, Deserialize, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct AbilityId(u32);

/// Upgrade
#[derive(Debug, Serialize, Deserialize, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct UpgradeId(u32);

impl UnitTypeId {
    /// Create new id from u32
    pub fn new(v: u32) -> Self {
        UnitTypeId(v)
    }
}

impl AbilityId {
    /// Create new id from u32
    pub fn new(v: u32) -> Self {
        AbilityId(v)
    }
}

impl UpgradeId {
    /// Create new id from u32
    pub fn new(v: u32) -> Self {
        UpgradeId(v)
    }
}
