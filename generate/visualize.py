from pathlib import Path
import subprocess as sp

GV_DOT_DIR = Path("generated") / "visuals"


def visualize():
    for p in GV_DOT_DIR.iterdir():
        if p.is_file() and p.suffix == ".dot":
            sp.run(
                ["dot", "-Tpng", str(p), "-o", str(p.with_suffix(".png"))], check=True
            )


if __name__ == "__main__":
    visualize()
