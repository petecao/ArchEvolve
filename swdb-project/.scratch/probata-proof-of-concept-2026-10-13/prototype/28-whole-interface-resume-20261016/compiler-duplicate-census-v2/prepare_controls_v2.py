"""Author pure controls only; never invoke a retained reader or bootstrap."""
from pathlib import Path
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'compiler-duplicate-census-v1'
test=(OLD/'test_complete_census_v1.py').read_text().replace('complete_duplicate_census_v1.py','complete_duplicate_census_v2.py')
before="self.assertNotEqual(item['first_value']['ordered_merkle_sha256'],item['next_value']['ordered_merkle_sha256'])"
after="self.assertNotEqual(item.get('first_value',{}).get('ordered_merkle_sha256',item.get('first_value_merkle_sha256')),item.get('next_value',{}).get('ordered_merkle_sha256',item.get('next_value_merkle_sha256')))"
assert test.count(before)==1;test=test.replace(before,after,1)
extra='''    def test_full_long_key_and_kind_identities_never_group_by_display_prefix(self):
        common='x'*256;names=[common+'a',common+'b']
        nodes=[[('kind',js('Unknown')), (key,js(1)), (key,js(2))] for key in names]
        r=census(tu(nodes));self.assertEqual(r['duplicate_events'],2);self.assertEqual(r['duplicate_group_count'],2)
        self.assertEqual({g['signature']['key_sha256'] for g in r['duplicate_groups']},{hashlib.sha256(k.encode()).hexdigest() for k in names})
        kinds=['K'*128+'a','K'*128+'b'];nodes=[[('kind',js(kind)),('x',js(1)),('x',js(2))] for kind in kinds]
        r=census(tu(nodes));self.assertEqual(r['duplicate_group_count'],2)
        self.assertEqual({g['signature']['node_kind_identity']['decoded_string_sha256'] for g in r['duplicate_groups']},{hashlib.sha256(k.encode()).hexdigest() for k in kinds})
    def test_worst_case_publication_extent_keeps_complete_digests_and_input_unchanged(self):
        report=census(tu([node()]));value={'census':report,'inputs':[{'path':'p'*300,'sha256':'f'*64} for _ in range(8)],'fixed':'f'*4096}
        report['samples']=[{'metadata':'x'*2000} for _ in range(8)]
        report['duplicate_groups']=[{'signature':'g'*980,'count':i} for i in range(16)]
        original=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
        text=S['publication'](value);self.assertLessEqual(len(text.encode())+1,32768);published=json.loads(text)
        self.assertEqual(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False),original)
        p=published['publication'];self.assertEqual(p['complete_report_sha256'],hashlib.sha256(original.encode()).hexdigest())
        self.assertEqual(p['complete_report_bytes'],len(original.encode()));self.assertGreater(p['omitted_group_display_rows']+p['omitted_event_display_rows'],0)
        self.assertEqual(p['omitted_event_display_rows']+len(published['census']['samples']),8)
        self.assertEqual(p['omitted_group_display_rows']+len(published['census']['duplicate_groups']),16)
        for key in ('duplicate_events','duplicate_group_count','duplicate_event_census_sha256','complete_duplicate_group_census_sha256','ordered_graph_merkle_sha256','original_minified_token_sha256','prospective_normalized_token_sha256'):
            self.assertEqual(published['census'][key],report[key])
        with self.assertRaises(S['Refused']):S['publication']({'census':report,'fixed':'x'*40000})
    def test_group_membership_is_order_independent_but_event_digest_is_ordered(self):
        a=[('kind',js('unknown')),('x',js(1)),('x',js(2))];b=[('kind',js('unknown')),('y',js(1)),('y',js(2))]
        left=census(tu([a,b]));right=census(tu([b,a]))
        self.assertEqual(left['complete_duplicate_group_census_sha256'],right['complete_duplicate_group_census_sha256'])
        self.assertNotEqual(left['duplicate_event_census_sha256'],right['duplicate_event_census_sha256'])
'''
assert test.count("if __name__=='__main__':")==1;test=test.replace("if __name__=='__main__':",extra+"if __name__=='__main__':")
(HERE/'test_complete_census_v2.py').write_text(test)
boot=(OLD/'test_readonly_bootstrap_v2.py').read_text().replace('readonly_bootstrap_v2.py','readonly_bootstrap_v3.py').replace('complete_duplicate_census_v1.py','complete_duplicate_census_v2.py')
size=(HERE/'complete_duplicate_census_v2.py').stat().st_size
assert boot.count('21433')==1 and boot.count('21434')==1
boot=boot.replace('21433',str(size)).replace('21434',str(size+1))
(HERE/'test_readonly_bootstrap_v3.py').write_text(boot)
