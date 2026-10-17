"""2026-10-16 ET. Synthetic syntax controls; no diagnostic main or remote read."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import unittest
EVENTS=[]
def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in ('os.system','ctypes.dlopen'):
        EVENTS.append(event);raise RuntimeError('synthetic control forbids '+event)
sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent
SOURCE=(HERE/'diagnostic-v3.py').read_bytes()
NS={'__name__':'inert_syntax_controls'};exec(compile(SOURCE,'inert-diagnostic-v3','exec'),NS)
Y={'__name__':'inert_original_reader'};exec(compile(NS['YAML_BYTES'],'inert-original-reader','exec'),Y)
class Controls(unittest.TestCase):
    def test_unchanged_frozen_reader(self):
        self.assertEqual(hashlib.sha256(NS['YAML_BYTES']).hexdigest(),'467cef5049fc30f730f0176f7db336952f6ce006ec11a9b2872abec9ca53daf9')
    def test_sha_guard_false_positive_classified_without_value(self):
        value='0b'+'a'*62;r=NS['locate'](('root:\n  sha256: '+value+'\n').encode(),Y['Reader'])
        self.assertFalse(r['parsed']);s=r['syntax_frames'][-1]['scalar_syntax'];self.assertTrue(s['hexadecimal_sha256_shape']);self.assertTrue(s['legacy_integer_guard_match']);self.assertFalse(s['binary_integer_shape']);self.assertNotIn(value,json.dumps(r))
    def test_actual_noncanonical_binary_not_mislabeled_as_sha(self):
        r=NS['locate'](b'root:\n  number: 0b101\n',Y['Reader']);s=r['syntax_frames'][-1]['scalar_syntax'];self.assertTrue(s['binary_integer_shape']);self.assertFalse(s['hexadecimal_sha256_shape'])
    def test_mapping_colon_context_contains_only_identifier_key_labels(self):
        marker='PRIVATE-CONTENT-DO-NOT-RETURN';r=NS['locate'](('root:\n  nested:\n    message: ok\n    '+marker+'\n').encode(),Y['Reader'])
        self.assertEqual(r['category'],'YAML mapping colon');self.assertEqual(r['candidate_line'],4);self.assertNotIn(marker,json.dumps(r));self.assertEqual(r['syntax_frames'][-1]['metadata_key_label'],'message');self.assertEqual(r['nearby_syntax'][2]['metadata_key_label'],'message')
    def test_literal_and_folded_styles_are_syntax_only(self):
        for value,style in [('|2-','literal'),('"secret"','double_quoted'),("'secret'",'single_quoted'),('[secret]','flow'),('','empty')]:
            result=NS['lexical_shape'](value);self.assertEqual(result['style'],style);self.assertNotIn('secret',json.dumps(result))
    def test_guard_and_read_functions_ast_unchanged(self):
        old=ast.parse((HERE.parent/'yaml-diagnostic-v1/diagnostic-v1.py').read_bytes());new=ast.parse(SOURCE)
        def funcs(tree):return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
        a,b=funcs(old),funcs(new)
        for name in ('need','stable','read','shape','audit'):self.assertEqual(a[name],b[name])
        self.assertEqual(set(b)-set(a),{'lexical_shape','syntax_context','nearby_syntax','census_row'})
    def test_complete_five_synthetic_failure_context_stays_under_output_cap(self):
        # Start with the complete actual V1 structural report, not a single row.
        report=json.loads((HERE.parents[3]/'evidence/t25-public-v4-yaml-diagnostic-actual-v1-20261016.json').read_bytes())
        seen={}
        normalized=[]
        for row in report['rows']:
            syntax=row['syntax']
            if syntax['parsed']:
                normalized.append(row);continue
            syntax.pop('nearby_shape')
            worst={'function':'block' if row['case']=='safe' else 'value','indent':2147483647,'metadata_key_label':'k'*64,'scalar_syntax':NS['lexical_shape']('0b'+'a'*62)}
            syntax['syntax_frames']=[worst]*4
            syntax['nearby_syntax']=[{'line':2147483647,'indent':2147483647,'characters':8388608,'sequence_marker':False,'contains_colon':True,'metadata_key_label':'k'*64,'value_style':'double_quoted'}]*5
            normalized.append(NS['census_row'](row['case'],row['phase'],row['input'],syntax,seen))
        report['rows']=normalized
        self.assertEqual(len(report['rows']),15)
        self.assertLess(len(json.dumps(report,sort_keys=True).encode()),24576)
        self.assertEqual(sum('syntax_context_reference' in r['syntax'] for r in normalized),3)

    def test_only_exact_syntax_contexts_are_deduplicated(self):
        first=NS['locate'](b'root:\n  number: 0b101\n',Y['Reader'])
        second=NS['locate'](b'root:\n  number: 0b111\n',Y['Reader'])
        seen={};a=NS['census_row']('safe','proof',{},first,seen);b=NS['census_row']('other','proof',{},first,seen);c=NS['census_row']('different','proof',{},second,seen)
        self.assertNotIn('syntax_context_reference',a['syntax']);self.assertEqual(b['syntax']['syntax_context_reference'],{'case':'safe','phase':'proof'});self.assertNotIn('syntax_context_reference',c['syntax'])

    def test_known_good_parse_and_no_children(self):
        self.assertTrue(NS['locate'](b'root:\n  value: ok\n',Y['Reader'])['parsed']);self.assertEqual(EVENTS,[])
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'date':'2026-10-16 ET','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'child_events':EVENTS,'diagnostic_main_executed':False,'remote_or_project_or_compiler_executed':False,'source_sha256':hashlib.sha256(SOURCE).hexdigest()}));sys.exit(not result.wasSuccessful())
