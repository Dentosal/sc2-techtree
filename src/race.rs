#![allow(missing_docs)]

use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize, Serialize, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Race {
    Protoss,
    Zerg,
    Terran,
    Neutral,
}
