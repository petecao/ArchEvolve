import ast,difflib,hashlib,json,os,pathlib
T=pathlib.Path('/private/tmp'); old=T/'lanl_sparse_retire_consumed_source_guard_20261008_a1_r3.py'; new=T/'lanl_sparse_retire_consumed_source_guard_20261008_a1_r4.py'
b=old.read_bytes(); assert len(b)==176656 and hashlib.sha256(b).hexdigest()=='5d752e2b5ff86e36777c156f995c7a78a30011b5f0cb62979ad4a442d8caf2c5'
s=b.decode()
def replace(a,c):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,c)
replace("        receipt_pin['format'] = 'swdb.library-preserving-sparse-retirement-guard.v1'\n        prior = self.sealed(receipt_pin, LIMITS['receipt_bytes'])\n", '''        receipt_pin['format'] = 'swdb.library-preserving-sparse-retirement-guard.v1'
        status_pin = bindings['status']; stdout_pin = bindings['stdout']
        control = P(status_pin['path']).parent
        require(control.parent == BASE and control.name.startswith('lanl17-detached-sparse-')
                and P(status_pin['path']) == control/'status.json'
                and P(stdout_pin['path']) == control/'guard.stdout',
                'original_default_history_wrapper_routes_changed')
        status = strict_json(self.pinned(status_pin, 16384))
        returned = strict_json(self.pinned(stdout_pin, LIMITS['receipt_bytes']))
        require(status['format'] == 'swdb.lanl17-detached-library-sparse-administration-status.v1'
                and status['sealed'] is False and status['state'] == 'guard_completed'
                and status['guard_exit_code'] == 0 and status['retire_requested'] is False
                and status['expected_primary'] == self.args.expected_primary
                and status['selected_rows'] == self.args.select and 'error_class' not in status
                and status['inputs']['guard']['sha256'] == self.own_sha
                and status['guard_stdout'] == stdout_pin
                and status['reviewed_plan'] == bindings['default_reviewed_plan']
                and re.fullmatch('a[1-9][0-9]*', status['guard_attempt']),
                'original_default_history_wrapper_status_changed')
        require(receipt_pin['path'] == str(BASE/('lanl-library-preserving-sparse-retirement-20261008-'
                                               +status['guard_attempt'])/'receipt.json')
                and returned['format'] == 'swdb.library-preserving-sparse-retirement-return.v1'
                and returned['path'] == receipt_pin['path']
                and returned['bytes'] == receipt_pin['bytes']
                and returned['sha256'] == receipt_pin['sha256']
                and returned['identity_sha256'] == receipt_pin['identity_sha256']
                and returned['admitted'] is True and returned['retired_count'] == 0
                and returned['failure'] is None, 'original_default_history_stdout_receipt_binding_changed')
        prior = self.sealed(receipt_pin, LIMITS['receipt_bytes'])
''')
replace("                'original_default_history_review_changed')\n        require(prior['admitted']", '''                'original_default_history_review_changed')
        prior_configuration = {k: v for k, v in prior_plan.items()
                               if k not in ('identity_sha256', 'parent_review_pin')}
        backlinks = []
        for key in ('control_siblings_complete_review', 'pending_alias_coverage_review',
                    'receipt_source_proofs_complete_review', 'original_raw_files_complete_review'):
            coverage = dict(prior_configuration[key])
            backlinks.append(coverage.pop('parent_review_identity_sha256'))
            prior_configuration[key] = coverage
        consumers = []
        for item in prior_configuration['relevant_privileged_consumers']:
            consumer = dict(item); backlinks.append(consumer.pop('parent_review_identity_sha256'))
            consumers.append(consumer)
        prior_configuration['relevant_privileged_consumers'] = consumers
        require(all(link == prior_review['identity_sha256'] for link in backlinks)
                and sha(canonical(prior_configuration)) == prior_review['reviewed_configuration_sha256'],
                'original_default_history_review_configuration_changed')
        wrapper_pin = status['inputs']['wrapper']
        require(any(all(pin[k] == wrapper_pin[k] for k in ('path', 'bytes', 'sha256'))
                    for pin in prior_plan['protected_file_pins']),
                'original_default_history_wrapper_source_not_original_plan_pinned')
        self.pinned(wrapper_pin, LIMITS['plan_bytes'])
        started = datetime.datetime.fromisoformat(prior['started_at'])
        finished = datetime.datetime.fromisoformat(prior['finished_at'])
        current = datetime.datetime.fromisoformat(self.facts['started_at'])
        checked = datetime.datetime.fromisoformat(prior_plan['checked_at'])
        require(all(value.tzinfo is not None for value in (started, finished, current, checked))
                and 0 <= (started-checked).total_seconds() <= 300
                and started <= finished <= current, 'original_default_history_chronology_changed')
        require(prior['admitted']''')
replace("            'original_guard_receipt_pin': receipt_pin,\n", "            'original_guard_receipt_pin': receipt_pin,\n            'original_default_status_pin': status_pin, 'original_default_stdout_pin': stdout_pin,\n")
out=s.encode();ast.parse(out)
fd=os.open(new,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'wb') as f:f.write(out);f.flush();os.fsync(f.fileno())
diff=''.join(difflib.unified_diff(b.decode().splitlines(True),s.splitlines(True),fromfile=old.name,tofile=new.name)).encode(); dp=T/'lanl17-sparse-retirement-guard-r4-complete-r3-derivation-20261008-a1.diff'
fd=os.open(dp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'wb') as f:f.write(diff);f.flush();os.fsync(f.fileno())
print(json.dumps({'source':{'path':str(new),'bytes':len(out),'sha256':hashlib.sha256(out).hexdigest()},'diff':{'path':str(dp),'bytes':len(diff),'sha256':hashlib.sha256(diff).hexdigest()},'target_main_run':False,'tests_run':False}))
