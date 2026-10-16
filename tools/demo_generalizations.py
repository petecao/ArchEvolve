"""Reproduce BFS and synthetic mixed-access generalization review artifacts."""
from hashlib import sha256
from pathlib import Path
import argparse
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tools.demo_hardware_planning import generate as planning_examples
from archevolve.parameter_cli import write_fresh


def generate():
    source=planning_examples();output={}
    for case in ('bfs','mixed'):
        for name in ('hardware-plan.yaml','generalization-proposals.yaml','generalization-queries.yaml','generalizations.md','generalizations.mmd'):
            output[case+'/'+name]=source[case+'/'+name]
    output['manifest.json']=json.dumps({'format':'optional-generalization-demo-v0.1',
        'planning_manifest':json.loads(source['manifest.json']),
        'note':'BFS source annotations plus a synthetic mixed example. No inferred hardware support, cost comparison or implementation.',
        'artifact_sha256':{n:sha256(t.encode()).hexdigest() for n,t in output.items()}},indent=2)+'\n'
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();files=generate();write_fresh(args.output_dir,files)
    print('Generated review-only generalization examples: '+str(args.output_dir))


if __name__=='__main__':main()
