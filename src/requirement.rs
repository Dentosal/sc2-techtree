use serde::{Deserialize, Serialize};

use crate::ids::*;

/// Requirement for an ability
#[derive(Debug, Serialize, Deserialize, Clone, PartialEq, Eq)]
pub enum Requirement {
    /// Requires the specified add-on
    #[serde(rename = "addon")]
    AddOn(UnitTypeId),
    /// Requires that this building is an add-on to the specified building
    #[serde(rename = "addon_to")]
    AddOnTo(UnitTypeId),
    /// Requires that building exists (and is complete)
    #[serde(rename = "building")]
    Building(UnitTypeId),
    /// Requires that an upgrade is completed
    #[serde(rename = "upgrade")]
    Upgrade(UpgradeId),
}
