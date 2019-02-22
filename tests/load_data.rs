use sc2_techtree::TechData;

use std::fs::File;
use std::io::prelude::*;

#[test]
fn load_data() {
    let mut f = File::open("data/data.json").expect("File not found");

    let mut contents = String::new();
    f.read_to_string(&mut contents).expect("Could not read");

    TechData::from_json(&contents).expect("Deserialization failed");
}
