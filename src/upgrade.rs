use serde::{Deserialize, Serialize};

use crate::ids::*;
use crate::Cost;

/// Upgrade
#[derive(Debug, Serialize, Deserialize, Clone, PartialEq, Eq)]
pub struct Upgrade {
    /// Id
    pub id: UpgradeId,
    /// Name
    pub name: String,
    /// Cost
    pub cost: Cost,
}
