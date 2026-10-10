"""Certification command procedures: one frozen version table per command family.

Created: 2026-10-05 ET (code-review fixes F1-F3, F10, C4, C10). Agent-decided under Yan-Ru's
delegation; revisable.

Before this module, every certify path chose its behavior with ``if version == ...`` cascades spread
over five modules, the command's ``sources_sha256`` hashed every file of ``library/dx100`` and
``library/native`` for every version (so a 1.5 edit changed the digest of a 1.3 run), version labels
were shared by command families that mean different things (candidate 1.2 and library-operation 1.2),
and two behavior changes kept their label (ticket 75's record ``b7954f4d`` says 1.4 but ran the 1.3
isolation path; commit 93a2a94 changed DX100 1.4 record-file naming).

Now:

* **One table per command family** (:data:`PROCEDURES`): candidate artifacts of DX100 contracts,
  native-CPU contracts, library operations, and lowerings with calibration. Each entry is a frozen
  :class:`CertifyProcedure` naming the evaluator entry point, the scan primitive set, the directive
  rule, the evaluator-owned driver, the legality rules, the evidence basis and the files that version
  reads. :func:`procedure` raises on an unknown version; nothing else in the certify code compares
  version strings.
* **Per-version source manifest** (:func:`manifest`): only the files that version reads, plus one row
  for the procedure's own definition. Its digest is the record's ``command.sources_sha256``; the rows
  are ``command.sources``. The kernel plug-in and its result check are recorded beside it
  (``command.kernel_sources``) but are not part of the version's identity (the kernel's identity is its
  correctness check, ADR 0001).
* **Frozen content.** ``CertifyProcedure.sources_sha256`` is the manifest digest the version was frozen
  at. A record says whether the code that ran is that content (``command.sources_match_version``), and
  ``tests/test_certification_procedures.py`` fails when code a version reads changes without a change
  to this table. Any behavior change gets a new version; a refactor that keeps behavior re-declares the
  digest here and says why in its ticket.
* **Record identity.** New records also carry ``command.family``, ``command.code`` (the git commit and
  whether the version's files differ from it) and, for library operations,
  ``command.library_operation_version``. :func:`classify` maps old records, which carry none of these,
  to their procedure through :data:`HISTORIC` and the alias table :data:`LEGACY_ALIASES` (keyed by
  family, label and ``sources_sha256``).
"""
from __future__ import annotations

import dataclasses
import importlib
import subprocess
from pathlib import Path
from types import MappingProxyType

from swdb import artifacts, paths
from swdb.cli import UsageError

CANDIDATE = 'candidate'                    # rewrite-contract candidate artifacts on the DX100 strict model
NATIVE = 'native'                          # rewrite contracts that pin a native-CPU candidate profile
LIBRARY_OPERATION = 'library_operation'    # `swdb certify ENTRY --profile P`
LOWERING = 'lowering_calibration'          # lowerings against reference semantics, and calibration
FAMILIES = (CANDIDATE, NATIVE, LIBRARY_OPERATION, LOWERING)


def strict_defines(wait_rule):
    """The strict-layer preprocessor flags of one wait rule (2026-10-09 ET; None: the old rule, no flag)."""
    if wait_rule is None:
        return ()
    if wait_rule == 'gem5':
        return ('-DSWDB_STRICT_WAIT_RULE_GEM5',)
    raise ValueError('unknown strict wait rule: ' + str(wait_rule))


@dataclasses.dataclass(frozen=True)
class CertifyProcedure:
    """One runnable version of one certify command family."""

    family: str
    version: str
    summary: str
    evaluate: str                   # evaluator entry point, 'module:function'
    evidence_basis: str             # ADR 0008: 'simulated' (functional model) or 'measured' (host CPU)
    scan: str | None                # scan primitive set: None, 'evaluator_1_3', 'evaluator_1_4', 'library_operation'
    directives: str | None          # None, 'pragma_omp_only' (native) or 'dx100_knob_defaults' (DX100 1.5+)
    driver: str | None              # 'plugin' (certification_drivers[version]), 'profile.<harness key>' or a library path
    legality: str | None            # None, 'v1' (ticket 68) or 'v2' (C4 knob spellings, C24 _Pragma controls)
    checkout_sources: tuple         # repository-relative files of this checkout the version reads
    library_sources: tuple          # files relative to the library root the version reads
    sources_sha256: str             # frozen manifest digest (see the module docstring)
    process_split: bool = False     # the candidate runs as the child of a trusted evaluator process (ticket 78)
    # 2026-10-09 ET: the strict layer's wait rule. None: a wait covers the tile's last writer and its
    # dependencies (spec.md:476-485, the rule of every version before candidate 1.7 and lowering 1.2).
    # 'gem5': the gem5 DX100 device's rule (research 14; strict header built with
    # -DSWDB_STRICT_WAIT_RULE_GEM5).
    wait_rule: str | None = None

    @property
    def scan_primitives(self):
        """The primitive names the version's scan refuses in candidate-authored text."""
        from swdb import certification_isolation as isolation
        if self.scan is None:
            return frozenset()
        if self.scan == 'evaluator_1_3':
            return frozenset(isolation.PRIMITIVES)
        if self.scan in ('evaluator_1_4', 'library_operation'):
            return frozenset(isolation.PRIMITIVES_1_4)
        raise ValueError('unknown scan primitive set: ' + self.scan)

    def entry_point(self):
        module, _, name = self.evaluate.partition(':')
        return getattr(importlib.import_module(module), name)

    def driver_path(self, library, plugin=None, profile=None):
        """The evaluator-owned driver (`main`) this version appends to a candidate, or None."""
        if self.driver is None:
            return None
        if self.driver == 'plugin':
            drivers = getattr(plugin, 'certification_drivers', None) or {}
            if self.version not in drivers:
                raise UsageError(f'kernel plug-in {getattr(plugin, "kernel", plugin)} declares no certification '
                                 f'driver for {self.family} {self.version}')
            return Path(library) / drivers[self.version]
        if self.driver.startswith('profile.'):
            return Path(profile[self.driver[len('profile.'):]]['driver'])
        return Path(library) / self.driver

    @property
    def strict_defines(self):
        """Preprocessor flags every strict-layer build of this version adds (2026-10-09 ET)."""
        return strict_defines(self.wait_rule)

    def definition(self):
        """The behavior-defining fields (not the summary or the frozen digest).

        2026-10-09 ET: ``wait_rule`` is left out while it is None, so the definition row (and digest) of
        every version frozen before it existed is unchanged."""
        return {field.name: getattr(self, field.name) for field in dataclasses.fields(self)
                if field.name not in ('summary', 'sources_sha256')
                and not (field.name == 'wait_rule' and self.wait_rule is None)}


# 2026-10-08 ET: re-declared after typed candidate refusals; standalone checks, messages,
# CLI categories, evaluator/control decisions and verdicts are unchanged. Campaign infrastructure
# interruption handling is outside these manifests. Dated before/after evidence:
# .scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-certification-fingerprint-redeclaration-20261008.md.

# --- the files each version reads ------------------------------------------------------------------------

_CORE = ('swdb/certification.py', 'swdb/certification_common.py', 'swdb/certification_faults.py',
         'swdb/certification_feedback.py', 'swdb/certification_isolation.py')
_LEGALITY = ('swdb/certification_legality.py',)
_BLINDING = ('swdb/certification_blinding.py',)
_PROCESS = ('swdb/certification_process.py',)
_NATIVE = ('swdb/certification_native.py',)
_STRICT = ('dx100/strict/MAA_functional.hpp', 'dx100/strict/gem5/m5ops.h')
_LOWERING_HEADER = ('dx100/dxc_lowering.hpp',)
_DX100_1_3 = tuple('dx100/certification/' + name for name in
                   ('candidate_prelude.hpp', 'record.cc', 'seams.cc', 'bfs_driver.inc', 'bc_driver.inc'))
_DX100_1_4 = tuple('dx100/certification/v1_4/' + name for name in
                   ('prelude.hpp', 'record.cc', 'seams.cc', 'bfs_driver.inc', 'bc_driver.inc'))
_DX100_1_5 = tuple('dx100/certification/v1_4/' + name for name in ('prelude.hpp', 'record.cc', 'seams.cc')) + \
    tuple('dx100/certification/v1_5/' + name for name in
          ('prelude.hpp', 'arena.hpp', 'client.cc', 'client_core.inc', 'client/MAA_functional.hpp', 'evaluator.cc',
           'evaluator_core.inc', 'evaluator_context.hpp', 'bfs_driver.inc', 'bc_driver.inc'))
_NATIVE_1_3 = ('native/certification/candidate_prelude.hpp', 'native/certification/record.cc',
               'native/certification/seams.cc', 'dx100/certification/bfs_driver.inc')
_NATIVE_1_4 = ('native/certification/v1_4/prelude.hpp', 'native/certification/v1_4/record.cc',
               'native/certification/v1_4/seams.cc', 'dx100/certification/v1_4/bfs_driver.inc')
_NATIVE_1_5 = _NATIVE_1_4[:3] + ('native/certification/v1_5/client.cc', 'native/certification/v1_5/evaluator.cc') + \
    tuple('dx100/certification/v1_5/' + name for name in
          ('arena.hpp', 'client_core.inc', 'evaluator_core.inc', 'evaluator_context.hpp', 'bfs_driver.inc'))
_EXTENSA = tuple('swdb/extensa/' + name for name in
                 ('profiles.py', 'probes.py', 'synthesis/certify.py', 'synthesis/differential_oracle.py',
                  'synthesis/families.py', 'synthesis/shape_classes.py', 'synthesis/spec.py',
                  'synthesis/targets/base.py', 'synthesis/targets/cpu_like.py'))
_LOP = ('swdb/library_operations.py',) + _EXTENSA
_LOP_RECORDS = ('swdb/library_operation_blinding.py', 'swdb/certification_isolation.py', 'swdb/certification_faults.py')


def _candidate(version, summary, evaluate, scan, directives, legality, extra_python, library, digest, wait_rule=None):
    return CertifyProcedure(CANDIDATE, version, summary, evaluate, 'simulated', scan, directives, 'plugin', legality,
                            _CORE + _LEGALITY + extra_python, _STRICT + _LOWERING_HEADER + library, digest,
                            process_split=_PROCESS[0] in extra_python, wait_rule=wait_rule)


def _native(version, summary, evaluate, scan, driver, extra_python, library, digest):
    return CertifyProcedure(NATIVE, version, summary, evaluate, 'measured', scan, 'pragma_omp_only', driver, None,
                            _CORE + _NATIVE + extra_python, library, digest, process_split=_PROCESS[0] in extra_python)


def _lop(version, summary, extra_python, extra_checkout, library, digest):
    return CertifyProcedure(LIBRARY_OPERATION, version, summary, 'swdb.library_operations:evaluate_procedure',
                            'measured', None if version == '1.0' else 'library_operation', None, None, None,
                            _LOP + extra_python + extra_checkout, library, digest, process_split=version == '1.2')


# 2026-10-06 ET: re-declared after JSON attribution serialization (bb7673f) and shared
# record-reader/hash delegation (bb11cb1); procedure decisions and evaluator files are unchanged.
# Evidence: .scratch/lanl-db-analytic-eval-2026-10-06/evidence/09-certification-fingerprint-redeclaration.md.
# 2026-10-09 ET: re-declared after the gem5 wait-rule switch (candidate 1.7, lowering 1.2): only the bytes of
# swdb/certification.py, swdb/certification_process.py and library/dx100/strict/MAA_functional.hpp changed;
# without -DSWDB_STRICT_WAIT_RULE_GEM5 the strict header preprocesses to identical text, every old code
# path is unchanged and every definition row is unchanged. Evidence:
# .scratch/formal-verification-2026-10-09/evidence/strict-gem5-wait-rule-redeclaration-20261009.md.
PROCEDURES = MappingProxyType({
    CANDIDATE: MappingProxyType({
        '1.3': _candidate('1.3', 'ticket 70: evaluator records on a descriptor, faults in a separate seam object per '
                          'control, evaluator scan', 'swdb.certification:certify_candidate', 'evaluator_1_3', None,
                          'v1', (), _DX100_1_3,
                          'f6d59b94a759750d994e7679ddc14e64b1f0846a52d6cae90905cabc37787704'),
        '1.4': _candidate('1.4', 'ticket 76: one binary per tile size, blinded run plan, random order, attributed '
                          'rejections, slide-window seam witness', 'swdb.certification_blinding:certify_candidate',
                          'evaluator_1_4', None, 'v1', _BLINDING, _DX100_1_4,
                          'd4a02b7285d3580af267792209e41480dc018769684554af71ef88f31a282e73'),
        '1.5': _candidate('1.5', 'ticket 78: 1.4 with record-keeping in a separate evaluator process; DX100 '
                          'directive rule', 'swdb.certification_process:certify_candidate', 'evaluator_1_4',
                          'dx100_knob_defaults', 'v1', _BLINDING + _PROCESS, _DX100_1_5,
                          'e2d1413bb5831ad4e0e77cfacbd88813dbc9721d0f66e93fa03248ca810e5373'),
        '1.6': _candidate('1.6', '2026-10-05 review fixes: 1.5 with knob_range reading every declared knob spelling '
                          'the candidate uses (unverified when none is used, never the default) and the '
                          'schedule_out_of_range control also mutating _Pragma forms',
                          'swdb.certification_process:certify_candidate', 'evaluator_1_4', 'dx100_knob_defaults',
                          'v2', _BLINDING + _PROCESS, _DX100_1_5,
                          '81e4697dcd77d60c5f96d191ddfa7c562e7b562e94d826cb1c51215ad1adc642'),
        # 2026-10-09 ET (Yan-Ru's request): research 14 refuted the old wait rule on gem5's DX100 device.
        '1.7': _candidate('1.7', '2026-10-09: 1.6 with the gem5 DX100 wait rule in the evaluator\'s strict layer '
                          '(a wait covers every uncovered command naming the tile as src1/src2/dst1/dst2, '
                          'transitively except through a filled range loop\'s tile inputs; a constant write '
                          'waits for the register\'s readers; issuing a command first covers the users of its destination '
                          'tile, the dispatch stall of IF.cc:193-212; research 14)',
                          'swdb.certification_process:certify_candidate', 'evaluator_1_4', 'dx100_knob_defaults',
                          'v2', _BLINDING + _PROCESS, _DX100_1_5,
                          '9dedc2a90485df95875a3dd7bae99ed870ed89cf7841d59b1a1c8e02b213cf04', wait_rule='gem5'),
    }),
    NATIVE: MappingProxyType({
        '1.3': _native('1.3', 'ticket 75: native-CPU profile under 1.3 isolation (a seam object per fault)',
                       'swdb.certification_native:certify_native', 'evaluator_1_3', 'profile.harness', (), _NATIVE_1_3,
                       '4b32c8f9c3b687c290ef33fd1bc8f479fc13523e83f4fa7ca7d759d0531adcff'),
        '1.4': _native('1.4', 'ticket 75 after ticket 76: one binary per build, blinded plan, attributed rejections',
                       'swdb.certification_native:certify_native_v14', 'evaluator_1_4', 'profile.harness_v14',
                       _BLINDING, _NATIVE_1_4,
                       '98c68dbf244c6c98116473839631643d315d977c51659d90e9bc4a2b24e0249a'),
        '1.5': _native('1.5', 'ticket 78: native 1.4 with record-keeping in a separate evaluator process',
                       'swdb.certification_process:certify_native', 'evaluator_1_4',
                       'dx100/certification/v1_5/bfs_driver.inc', _BLINDING + _PROCESS, _NATIVE_1_5,
                       '26d3fce0ffd8de603cc624945dae88eaec3d47ab9d34a3b1708c787e862d87af'),
    }),
    LIBRARY_OPERATION: MappingProxyType({
        '1.0': _lop('1.0', 'tickets 49-51: the ported two-binary harness; a control abort classified from a '
                    'printed line', (), (), (),
                    '7ffd0a8f3ff6e2fa0da4c966010c5a57a0378140a5a6c777c32fbcd4d3fa8dea'),
        '1.1': _lop('1.1', 'ticket 77: records from a trusted driver, reference first, blinded driver faults, '
                    'attributed controls, scan', _LOP_RECORDS, (),
                    ('library_operations/certification/v1_1/record.cc',
                     'library_operations/certification/v1_1/driver.cc'),
                    '4cf8263345419fc5442d5aae5fb7f2a358c08b4d4052f90f7a3b2462fc9710b7'),
        '1.2': _lop('1.2', 'ticket 78: 1.1 with the call in a separate candidate process', _LOP_RECORDS,
                    ('library/dx100/certification/v1_5/arena.hpp',),
                    ('library_operations/certification/v1_1/record.cc',
                     'library_operations/certification/v1_2/evaluator.cc',
                     'library_operations/certification/v1_2/runner.cc',
                     'library_operations/certification/v1_2/call.hpp'),
                    'a8cb6f19a83cf8ba530f6209b898af7b8985256665633c9e78c8f4ad9821cb91'),
    }),
    LOWERING: MappingProxyType({
        '1.1': CertifyProcedure(LOWERING, '1.1', 'lowerings: pinned differential driver against reference semantics; '
                                'calibration: the authors\' tree; printed named checks of trusted code only (ticket '
                                '76); calibration control rule of 2026-10-04 (8040609)',
                                'swdb.certification:evaluate_trusted', 'simulated', None, None, None, None,
                                ('swdb/certification.py',), _STRICT,
                                'bd98d8640a24635101802b26be5de970f3ec7be0905ae79bd2f989e873d6c4bf'),
        # 2026-10-09 ET (Yan-Ru's request): 1.1 with the gem5 DX100 wait rule (research 14). Calibration
        # certifies the unmodified authors' TDStepMAA (no tile3 -> tile5 patch); its store-wait control is
        # dropped_store_wait (the wait deleted). Lowering controls the new rule accepts are replaced.
        '1.2': CertifyProcedure(LOWERING, '1.2', 'lowerings and calibration as 1.1 with the gem5 DX100 wait rule '
                                '(research 14, with the dispatch stall on tiles): calibration of the unmodified authors\' source, '
                                'controls the rule '
                                'accepts replaced (wrong_store_wait -> dropped_store_wait, constant_uncovered '
                                'dropped or replaced)',
                                'swdb.certification:evaluate_trusted_gem5_wait', 'simulated', None, None, None, None,
                                ('swdb/certification.py',), _STRICT,
                                '0c9bab290e8d46c7bd7a9f7a4a23f751bb910353b5005264e81de1cb61dd41b3', wait_rule='gem5'),
    }),
})

#: The version each family runs when none is given.
# 2026-10-09 ET: candidate 1.7 and lowering 1.2 (gem5 wait rule) are the defaults; 1.3-1.6 and 1.1 stay runnable.
DEFAULTS = MappingProxyType({CANDIDATE: '1.7', NATIVE: '1.5', LIBRARY_OPERATION: '1.2', LOWERING: '1.2'})

#: Labels that appear in records but name no runnable procedure (their code is gone).
HISTORIC = MappingProxyType({
    CANDIDATE: MappingProxyType({
        '1.0': 'tickets 18-62: named checks read from printed output; forged_frontier v1',
        '1.1': 'ticket 67: forged_frontier v2',
        '1.2': 'ticket 68: knob_range and schedule_range (SWDB_KNOB_<NAME> only)',
    }),
    LOWERING: MappingProxyType({
        '1.0': 'records of 2026-10-03, labeled with the candidate command version of the day; calibration controls '
               'before the 2026-10-04 control rule (8040609)',
    }),
})

# DX100 candidate code whose 1.4 or 1.5 runs named record files by cell or control (before 93a2a94):
# the sources_sha256 each commit's own code records (computed from those commits, 2026-10-05 ET).
_CELL_NAMED_1_4 = {'29f3bcab362c7c830f0030122aae1b3382c1eb83be3171f1a91b62a690724be1': 'c2fb788',
                   'd9b414cb2f2ebf3e2eabccff02f3d74e7a7be9f90b0724e211f51576fd7efa81': '9490d57',
                   '28529e9823e38cbd64f70b24e83d27da13436bb08954f3b9c2aa4e21568c8a8d': '537818e',
                   '3c89c471a8711a246ae164fa4a5f47ab679f3984a085892cf3bc6523c3c843b4': 'be156e8',
                   '5605e1f037857ac90126c7acfe14a0785fa31377c95ceca4c97bb02289f65db5': '8c08fe6',
                   '865781417754167dad648133fc09e967413d07e8c67e394a39ee57b81ee6789b': '12ec6fe',
                   '240b91cfd3f48d51ad3f979c690902713717eb9baa2f273f15e75546d0ee58e8': 'ce6e6e9',
                   '9b75b279b582b8a312d1738bb0983cfcde19cd69d400ad4614939e908e7a363f': '9e267fd'}
_PROTOTYPE_1_5 = ('865781417754167dad648133fc09e967413d07e8c67e394a39ee57b81ee6789b',
                  '240b91cfd3f48d51ad3f979c690902713717eb9baa2f273f15e75546d0ee58e8',
                  '9b75b279b582b8a312d1738bb0983cfcde19cd69d400ad4614939e908e7a363f')


def _aliases():
    rows = {(NATIVE, '1.4', '06fe4cc53b3b69254a457dd5b8a43031da60b3fe04bcd34cc6e42a50b1ef7cc9'): {
        'procedure': '1.3', 'variant': None,
        'note': 'ticket 75 branch at 6e1fe61 numbered its 1.3-isolation native path "1.4" before the ticket 76 merge '
                '(record certification.b7954f4df9dd4e228fb12437b845f190)'}}
    for digest, commit in _CELL_NAMED_1_4.items():
        rows[(CANDIDATE, '1.4', digest)] = {
            'procedure': '1.4', 'variant': 'cell_named_record_files',
            'note': f'DX100 1.4 at {commit}: record files named by cell or control, so the descriptor path named the '
                    'fault (renamed by nonce in 93a2a94 without a version change)'}
    for digest in _PROTOTYPE_1_5:
        rows[(CANDIDATE, '1.5', digest)] = {
            'procedure': '1.5', 'variant': 'prototype_cell_named_no_directive_rule',
            'note': f'DX100 1.5 prototype at {_CELL_NAMED_1_4[digest]}: cell-named record files and no directive rule '
                    '(both added in 93a2a94 without a version change)'}
    return MappingProxyType(rows)


#: (family, recorded label, recorded sources_sha256) -> the procedure that actually ran (C10).
LEGACY_ALIASES = _aliases()


def procedure(family, version=None):
    """The runnable procedure of one family; an unknown or historic version raises UsageError."""
    if family not in PROCEDURES:
        raise UsageError('unknown certify command family: ' + str(family))
    version = version or DEFAULTS[family]
    table = PROCEDURES[family]
    if version not in table:
        historic = HISTORIC.get(family, {}).get(version)
        label = family.replace('_', ' ')
        if historic:
            raise UsageError(f'{label} certify command {version} is historic ({historic}); runnable versions: '
                             + ', '.join(table))
        raise UsageError(f'{label} certify command version must be one of ' + ', '.join(table) + f', not {version}')
    return table[version]


def all_versions():
    """Every runnable label of every family (the CLI's --command-version choices)."""
    return tuple(sorted({v for table in PROCEDURES.values() for v in table}, key=lambda v: tuple(map(int, v.split('.')))))


# --- manifests -------------------------------------------------------------------------------------------

def _row(path, label):
    path = Path(path)
    return {'path': label, 'sha256': artifacts.file_hash(path) if path.is_file() else None}


def definition_sha256(proc):
    return artifacts.digest(proc.definition())


def manifest(proc, library_root, plugin=None):
    """{sources, sources_sha256, kernel_sources, files} of one procedure (files: absolute paths read)."""
    library_root = Path(library_root)
    files = [paths.HOME / rel for rel in proc.checkout_sources] + [library_root / rel for rel in proc.library_sources]
    rows = [_row(paths.HOME / rel, rel) for rel in proc.checkout_sources]
    rows += [_row(library_root / rel, 'library/' + rel) for rel in proc.library_sources]
    rows.append({'path': f'swdb/certification_procedures.py#{proc.family}/{proc.version}',
                 'sha256': definition_sha256(proc)})
    kernel = []
    if plugin is not None:
        module = Path(importlib.import_module(type(plugin).__module__).__file__)
        package = Path(importlib.import_module('swdb.kernels').__file__)
        for path in (package, module):
            kernel.append(_row(path, 'swdb/kernels/' + path.name))
            files.append(path)
        verifier = getattr(plugin, 'native_verifier', None)
        if verifier:
            kernel.append({'path': 'result_check:' + verifier, 'sha256': plugin.native_verifier_sha256()})
    return {'sources': rows, 'sources_sha256': artifacts.digest(rows), 'kernel_sources': kernel, 'files': files}


def unchanged(before, after):
    """True when no file of a manifest changed between two snapshots of it (during-run check)."""
    return (before['sources'] == after['sources'] and before['kernel_sources'] == after['kernel_sources'])


def code_identity(files):
    """{git_commit, sources_differ_from_commit} for the files of this checkout a run read (None outside git)."""
    repo = paths.HOME
    inside = sorted({str(Path(f).resolve().relative_to(repo.resolve())) for f in files
                     if Path(f).resolve().is_relative_to(repo.resolve())})
    try:
        commit = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], capture_output=True, text=True,
                                timeout=30)
        if commit.returncode:
            return {'git_commit': None, 'sources_differ_from_commit': None}
        status = subprocess.run(['git', '-C', str(repo), 'status', '--porcelain', '--', *inside],
                                capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return {'git_commit': None, 'sources_differ_from_commit': None}
    return {'git_commit': commit.stdout.strip(),
            'sources_differ_from_commit': bool(status.stdout.strip()) if status.returncode == 0 else None}


def command_fields(proc, library_root, plugin=None):
    """The `command` fields every new record of this procedure carries (before the run)."""
    found = manifest(proc, library_root, plugin)
    fields = {'version': proc.version, 'family': proc.family, 'sources_sha256': found['sources_sha256'],
              'sources': found['sources'], 'sources_match_version': found['sources_sha256'] == proc.sources_sha256,
              'code': code_identity(found['files'])}
    if found['kernel_sources']:
        fields['kernel_sources'] = found['kernel_sources']
    if proc.family == LIBRARY_OPERATION:
        fields['library_operation_version'] = proc.version
    return fields, found


# --- old records (C10) --------------------------------------------------------------------------------------

def record_family(record):
    """The command family of a certification record, new or old."""
    command = record.get('command') or {}
    if command.get('family') in FAMILIES:
        return command['family']
    if command.get('kind') == 'library_operation_differential':
        return LIBRARY_OPERATION
    if record.get('profile'):
        return NATIVE
    if record.get('candidate'):
        return CANDIDATE
    return LOWERING


def classify(record):
    """{family, label, procedure, variant, runnable, note} of one certification record.

    ``procedure`` is the version whose behavior the record shows, which differs from its label for the
    records in :data:`LEGACY_ALIASES`."""
    family = record_family(record)
    command = record.get('command') or {}
    label = command.get('library_operation_version') or command.get('version')
    alias = LEGACY_ALIASES.get((family, label, command.get('sources_sha256')))
    if alias:
        return {'family': family, 'label': label, 'procedure': alias['procedure'], 'variant': alias['variant'],
                'runnable': False, 'note': alias['note']}
    if label in PROCEDURES[family]:
        return {'family': family, 'label': label, 'procedure': label, 'variant': None, 'runnable': True,
                'note': PROCEDURES[family][label].summary}
    note = HISTORIC.get(family, {}).get(label)
    return {'family': family, 'label': label, 'procedure': label if note else None, 'variant': None,
            'runnable': False, 'note': note or 'unknown label'}
