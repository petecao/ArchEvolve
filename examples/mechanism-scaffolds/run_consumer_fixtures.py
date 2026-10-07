"""Compile/run the bounded SMASH and HTA consumer witnesses, not hardware."""
import argparse
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--compiler", default="g++")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parent
    results = []
    for design, filename in (("smash", "consumer_fixture.cc"), ("hta", "recheck_fixture.cc")):
        binary = args.output_dir / design
        command = [args.compiler, "-std=c++17", "-O1", "-Wall", "-Wextra", "-Werror",
                   "-fsanitize=undefined", "-fno-sanitize-recover=all", "-pthread",
                   str(root / design / filename), "-o", str(binary)]
        subprocess.run(command, check=True)
        subprocess.run([str(binary)], check=True)
        results.append({"fixture": design, "command": command, "compile_rc": 0, "run_rc": 0})
    print(json.dumps({"status": "HOST_CONSUMER_FIXTURES_PASS", "results": results,
                      "hardware_certificate": False}, indent=2))


if __name__ == "__main__":
    main()
