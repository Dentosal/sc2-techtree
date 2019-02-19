//! Cost of an action

use noisy_float::prelude::*;
use serde::{Deserialize, Serialize};

/// Cost
#[derive(Debug, Serialize, Deserialize, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub struct Cost {
    // Mineral cost
    minerals: u32,
    // Vespene gas cost
    gas: u32,
    // Time cost
    time: Option<R32>,
}
impl Cost {
    /// Is the action free (by mineral cost)
    pub fn is_free(&self) -> bool {
        self.minerals == 0 && self.gas == 0
    }
}
