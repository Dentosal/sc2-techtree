use sc2_techtree as sc2tech;

use std::env;
use std::fs::File;
use std::io::prelude::*;

use serde_json;

fn main() {
    for (i, filename) in env::args().enumerate().skip(1) {
        let mut f = File::open(filename).expect("File not found");

        let mut contents = String::new();
        f.read_to_string(&mut contents).expect("Could not read");

        let _: sc2tech::TechData = serde_json::from_str(&contents).expect("Invalid data");
        println!("File {}: ok", i);
    }
}
