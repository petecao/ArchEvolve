"""Reproduce the real-contract, unvalidated six-point DX100 candidate bundle."""
from pathlib import Path
import argparse
import sys
import yaml

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from archevolve.__main__ import prepare_run
from archevolve.dx100_parameter_adapter import prepare_candidates
from archevolve.parameter_cli import write_fresh


def generate():
    forward,manifest=prepare_run([ROOT/'examples/received/bfs-sparse.features.v1.2.yaml'],
        ROOT/'catalog/hardware-v0.1.yaml',max_candidates=2,
        source_context_path=ROOT/'examples/bfs.source-observations.yaml',focus_design_ids=['dx100-artifact-e4fc4af'])
    candidate=yaml.safe_load(forward['case-01/handoffs/candidate-02/candidate.yaml'])
    handoff=ROOT/'docs/designs/dx100-parameter-domain'
    return prepare_candidates(candidate,manifest['cases'][0]['input_sha256'],manifest['identity']['catalog_sha256'],
        handoff/'contract.yaml',handoff/'verification.json',handoff/'published-dx100-calibration.json')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    files,plan=generate();write_fresh(args.output_dir,files)
    print(f"Generated {plan['candidate_count']} pending candidates, zero admitted configurations: {args.output_dir/'README.md'}")


if __name__=='__main__':main()
