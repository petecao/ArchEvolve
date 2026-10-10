import ast,difflib,hashlib,json,os,pathlib
T=pathlib.Path('/private/tmp'); old=T/'lanl_sparse_retire_consumed_source_guard_20261008_a1_r2.py'; new=T/'lanl_sparse_retire_consumed_source_guard_20261008_a1_r3.py'
b=old.read_bytes(); assert len(b)==166145 and hashlib.sha256(b).hexdigest()=='4956a7453ae569d7ccf6e1a9ed98a1a933bee2e35cca1774932afbfba819bd26'
s=b.decode()
def replace(a,c):
 global s
 assert s.count(a)==1,(a,s.count(a)); s=s.replace(a,c)
replace('Default is a full read-only storage assessment with fresh administrative custody.', 'Default is a read-only metadata/source-proof assessment with fresh administrative\ncustody. Full tracked regular-file byte checks are deferred to each actual\nretirement. Original historical bytes may be inherited only from an accepted\nexact-source DEFAULT receipt with unchanged complete file identities.')
replace('        self.passive_hashes = {}\n', '        self.passive_hashes = {}\n        # Inherited original history is separate from fresh byte-read caches.\n        self.inherited_history = {}\n        self.parent_review = None\n')
replace('    def pin_fact(self, pin):\n        # Only an already-byte-checked, stable baseline file can use this cache.\n', '''    def pin_fact(self, pin):
        if pin['path'] in self.inherited_history:
            witness = self.inherited_history[pin['path']]
            require(pin['bytes'] == witness['bytes'] and pin['sha256'] == witness['sha256']
                    and pin.get('stat') == witness['stat'], 'inherited_history_pin_changed')
            self.check_inherited_history_file(witness)
            return
        # Only an already-byte-checked, stable baseline file can use this cache.
''')
replace('        # Explicit parent source-byte proofs, when claimed by original receipts.\n', '        # One fresh parsed original per receipt in this call; every reused proof\n        # retains a complete file-identity check and its own exact JSON field.\n        receipt_documents = {}\n        # Explicit parent source-byte proofs, when claimed by original receipts.\n')
replace("            doc = strict_json(self.read(PRIMARY/EVIDENCE/RECEIPTS[proof['receipt_key']]['file'],\n                                        LIMITS['inventory_bytes'])[0])\n", '''            receipt_key = proof['receipt_key']
            receipt_path = PRIMARY/EVIDENCE/RECEIPTS[receipt_key]['file']
            if receipt_key not in receipt_documents:
                receipt_body, receipt_stat = self.read(receipt_path, LIMITS['inventory_bytes'])
                require(sha(receipt_body) == RECEIPTS[receipt_key]['sha256'],
                        'source_proof_original_receipt_bytes_changed')
                receipt_documents[receipt_key] = (strict_json(receipt_body), receipt_stat)
            doc, receipt_stat = receipt_documents[receipt_key]
            require(stamp(receipt_path.lstat()) == receipt_stat,
                    'source_proof_cached_original_receipt_changed')
''')
replace('        for path,expected in self.passive_stats.items():\n', '        for witness in self.inherited_history.values():\n            self.check_inherited_history_file(witness)\n        for path,expected in self.passive_stats.items():\n')
replace("        trees = {p.name: self.tree(p, ROWS[p.name]['head'],hash_regular_bytes=not self.args.retire)\n", "        # Both modes begin with metadata only. Each actual retirement has its\n        # separate mandatory fresh full regular-byte/Git-blob check.\n        trees = {p.name: self.tree(p, ROWS[p.name]['head'],hash_regular_bytes=False)\n")
replace("        require(all(link == review['identity_sha256'] for link in review_links),\n                'excluded_parent_review_link_not_bound')\n", "        require(all(link == review['identity_sha256'] for link in review_links),\n                'excluded_parent_review_link_not_bound')\n        self.parent_review = review\n")
replace('        self.load_retirement_inputs()\n        first = self.gate()\n', '        self.load_retirement_inputs()\n        self.inherit_historical_custody()\n        first = self.gate()\n')
replace("        self.facts['retired_rows']=self.completed_names()\n        self.facts['admitted']=True\n", "        self.record_historical_custody()\n        self.facts['retired_rows']=self.completed_names()\n        self.facts['admitted']=True\n")
methods='''    def historical_custody_projection(self):
        # Preserve every original semantic handling/basis and physical pin.
        return sorted(self.plan['historical_reference_files'], key=lambda pin: pin['path'])

    def historical_custody_eligible_paths(self):
        roots = {str(RAW/name) for row in RECEIPTS.values() for name in row['raw_names']}
        roots.update(self.plan['raw_control_sibling_paths'])
        # RAW/PRIMARY and candidate source bodies always keep their fresh checks.
        return {pin['path'] for pin in self.historical_custody_projection()
                if inside(pin['path'], RAW) and not any(inside(pin['path'], P(root)) for root in roots)}

    def check_inherited_history_file(self, witness):
        self.left(); self.stat_checks += 1
        require(self.stat_checks <= LIMITS['stat_checks'], 'inherited_history_stat_limit')
        p, observed = self.path(witness['path'])
        require(observed.st_nlink == 1 and observed.st_size == witness['bytes']
                and observed.st_size <= LIMITS['one_file']
                and stamp(observed) == witness['stat']
                and stamp(p.lstat()) == witness['stat'], 'inherited_history_file_identity_changed')

    def inherit_historical_custody(self):
        bindings = self.parent_review.get('successful_default_original_bindings')
        if not self.args.retire:
            require(bindings is None and self.parent_review.get('actual_default_only') is True,
                    'default_cannot_inherit_historical_byte_custody')
            return
        require(self.parent_review.get('actual_default_only') is False and type(bindings) is dict,
                'retirement_requires_original_default_history_custody')
        receipt_pin = dict(bindings['original_guard_receipt'])
        receipt_pin['format'] = 'swdb.library-preserving-sparse-retirement-guard.v1'
        prior = self.sealed(receipt_pin, LIMITS['receipt_bytes'])
        plan_pin = dict(bindings['default_reviewed_plan']['file'])
        plan_pin.update(identity_sha256=bindings['default_reviewed_plan']['identity_sha256'],
                        canonical_ensure_ascii=True,
                        format='swdb.library-preserving-sparse-retirement-parent-plan.v1')
        prior_plan = self.sealed(plan_pin, LIMITS['plan_bytes'])
        prior_review = self.sealed(prior_plan['parent_review_pin'], LIMITS['plan_bytes'])
        require(prior_review.get('actual_default_only') is True
                and prior_review['accepted_for_exact_subset'] is True
                and prior_review['accepted_library_preserving_sparse_scope'] is True
                and prior_review['final14_completed_and_released'] is True
                and bindings['default_review'] == prior_plan['parent_review_pin'],
                'original_default_history_review_changed')
        require(prior['admitted'] is True and prior['failure'] is None
                and prior['retire_requested'] is False and prior['retired_rows'] == []
                and prior['completed_retirements'] == [] and prior['pre_retire_full_byte_checks'] == {}
                and prior['full_raw_byte_passes'] == 2 and prior['inspection_limits'] == LIMITS
                and prior['scientific_admission'] is False and prior['capacity_admission'] is False
                and prior['guard_source_sha256'] == prior_plan['guard_source_sha256'] == self.own_sha
                and prior['expected_primary'] == prior_plan['expected_primary'] == self.args.expected_primary
                and prior['selected_rows'] == prior_plan['selected_rows'] == self.args.select
                and prior['reviewed_plan_file_sha256'] == plan_pin['sha256']
                and prior['reviewed_plan_identity_sha256'] == prior_plan['identity_sha256']
                and prior['parent_review_identity_sha256'] == prior_review['identity_sha256'],
                'original_default_history_receipt_scope_changed')
        for key, limit in (('bytes_read', 'total_file_bytes'), ('walk_entries_checked', 'walk_entries'),
                           ('stable_stat_checks', 'stat_checks')):
            require(type(prior[key]) is int and 0 <= prior[key] <= LIMITS[limit],
                    'original_default_history_counter_limit')
        for key in ('historical_reference_files', 'raw_control_sibling_paths', 'original_raw_file_pins',
                    'receipt_source_file_proofs', 'pending_control_files', 'future_source_pins',
                    'native_git_pin', 'account_service_identification_pin', 'portal_service_review_pin',
                    'retained_raw_library_aliases', 'retirement_operation'):
            require(prior_plan[key] == self.plan[key], 'original_default_history_coverage_changed')
        require(set(prior['initial_checks']['trees']) == set(self.args.select)
                and all(tree['regular_bytes_verified'] is False
                        and tree['tracked_mode_blob_source_inventory_sha256'] is None
                        for tree in prior['initial_checks']['trees'].values()),
                'original_default_deferred_tracked_byte_policy_changed')
        projection = self.historical_custody_projection()
        custody = prior['historical_byte_custody']
        require(custody['format'] == 'swdb.original-historical-byte-custody.v1'
                and custody['all_history_bytes_freshly_read_in_this_operation'] is True
                and custody['inherited_history_files'] == 0
                and custody['historical_projection_sha256'] == sha(canonical(projection)),
                'original_default_historical_byte_policy_changed')
        witnesses = custody['files']
        require(type(witnesses) is list and len(witnesses) == len(projection)
                and [x['path'] for x in witnesses] == [x['path'] for x in projection],
                'original_default_historical_witness_set_changed')
        eligible = self.historical_custody_eligible_paths()
        for pin, witness in zip(projection, witnesses):
            require(set(witness) == {'path', 'bytes', 'sha256', 'stat', 'reference_hits'}
                    and all(witness[k] == pin[k] for k in ('path', 'bytes', 'sha256', 'stat'))
                    and type(witness['reference_hits']) is bool,
                    'original_default_historical_witness_pin_changed')
            if pin['path'] in eligible:
                self.check_inherited_history_file(witness)
                self.inherited_history[pin['path']] = witness
        require(set(self.inherited_history) == eligible, 'inherited_history_exact_scope_required')
        self.facts['inherited_history_origin'] = {
            'original_guard_receipt_pin': receipt_pin,
            'original_default_plan_pin': plan_pin,
            'historical_projection_sha256': custody['historical_projection_sha256'],
            'files': len(eligible), 'bytes_previously_verified': sum(x['bytes'] for x in self.inherited_history.values()),
            'fresh_byte_read_in_this_operation_claimed': False,
            'unchanged_complete_file_identity_required_at_every_use_and_final': True}

    def record_historical_custody(self):
        projection = self.historical_custody_projection()
        if self.args.retire:
            for witness in self.inherited_history.values():
                self.check_inherited_history_file(witness)
            self.facts['historical_byte_custody'] = {
                'format': 'swdb.original-historical-byte-custody.v1',
                'historical_projection_sha256': sha(canonical(projection)),
                'all_history_bytes_freshly_read_in_this_operation': False,
                'inherited_history_files': len(self.inherited_history),
                'fresh_RAW_and_pre_retire_regular_byte_checks_preserved': True}
            return
        require(not self.inherited_history, 'default_historical_fresh_byte_proof_required')
        witnesses = []
        for pin in projection:
            self.pin_fact(pin)
            require(pin['path'] in self.passive_hashes, 'default_historical_byte_witness_missing')
            witnesses.append({'path': pin['path'], 'bytes': pin['bytes'],
                              'sha256': self.passive_hashes[pin['path']],
                              'stat': dict(self.passive_stats[pin['path']]),
                              'reference_hits': self.reference_hits[pin['path']]})
        self.facts['historical_byte_custody'] = {
            'format': 'swdb.original-historical-byte-custody.v1',
            'historical_projection_sha256': sha(canonical(projection)),
            'all_history_bytes_freshly_read_in_this_operation': True,
            'inherited_history_files': 0, 'files': witnesses}

'''
replace('    def stable_inventory(self):\n', methods+'    def stable_inventory(self):\n')
out=s.encode(); ast.parse(out)
fd=os.open(new,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'wb') as f:f.write(out);f.flush();os.fsync(f.fileno())
diff=''.join(difflib.unified_diff(b.decode().splitlines(True),s.splitlines(True),fromfile=old.name,tofile=new.name)).encode(); dp=T/'lanl17-sparse-retirement-guard-r3-complete-r2-derivation-20261008-a1.diff'
fd=os.open(dp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'wb') as f:f.write(diff);f.flush();os.fsync(f.fileno())
print(json.dumps({'source':{'path':str(new),'bytes':len(out),'sha256':hashlib.sha256(out).hexdigest()},'diff':{'path':str(dp),'bytes':len(diff),'sha256':hashlib.sha256(diff).hexdigest()},'target_main_run':False,'tests_run':False}))
