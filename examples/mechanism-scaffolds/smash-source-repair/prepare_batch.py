"""Portable entry for the exact-parent SMASH software repair batch."""
import importlib.util
from pathlib import Path

path = Path(__file__).parent / "smash_public_packed_capacity_2026_10_07/prepare_batch.py"
spec = importlib.util.spec_from_file_location("smash_repair_batch", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-a081", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(module.prepare(args.parent_a081, args.output), indent=2))
