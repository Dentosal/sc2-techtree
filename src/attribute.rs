#![allow(missing_docs)]

use serde::{Deserialize, Serialize};

/// Unit attributes
#[derive(Debug, Serialize, Deserialize, Clone, PartialEq, Eq, Hash)]
pub enum Attribute {
    Light,
    Armored,
    Detector,
    Structure,
    Massive,
    Biological,
    Mechanical,
    Psionic,
    Summoned,
}

/// Unit movement type
#[derive(Debug, Serialize, Deserialize, Clone, PartialEq, Eq, Hash)]
pub enum MovementType {
    Ground,
    Air,
    None,
}
