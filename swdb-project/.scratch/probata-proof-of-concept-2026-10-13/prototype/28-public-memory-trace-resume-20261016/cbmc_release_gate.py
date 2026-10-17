"""2026-10-16 ET. Pure future-successor CBMC exact-version gate; no probe.

The unchanged method's 6.11 family and root's exact observed full version are
separate pins. This helper never infers a runtime version from deployment paths.
"""
import hashlib
import re


def check_cbmc_version(policy, returncode, stdout, stderr):
    if not isinstance(policy, dict) or policy.get('accepted_cbmc_release_family') != '6.11':
        raise ValueError('unchanged method CBMC6.11 release family required')
    tools = policy.get('tools')
    if not isinstance(tools, dict) or not isinstance(tools.get('cbmc'), dict):
        raise ValueError('exact root-observed CBMC tool metadata is unknown')
    version = tools['cbmc'].get('version')
    if not isinstance(version, str) or re.fullmatch(r'6\.11(?:\.[0-9]+)?', version) is None:
        raise ValueError('exact root-observed CBMC6.11[.patch] version is unknown')
    if type(returncode) is not int or returncode != 0 or not isinstance(stdout, str) or not isinstance(stderr, str):
        raise ValueError('guarded CBMC version probe failed or lacks raw output')
    # Same primary numeric capture as swdb.cbmc_adapter.locate; reject malformed
    # extensions rather than silently admitting a truncated capture.
    match = re.match(r'\s*(\d+\.\d+(?:\.\d+)?)', stdout)
    if (match is None or match.group(1) != version or
            match.end() < len(stdout) and not stdout[match.end()].isspace()):
        raise ValueError('guarded CBMC version differs from exact admitted observation')
    return {'accepted_cbmc_release_family': '6.11', 'exact_observed_version': version,
            'stdout_sha256': hashlib.sha256(stdout.encode()).hexdigest(),
            'stderr_sha256': hashlib.sha256(stderr.encode()).hexdigest(),
            'returncode': returncode,
            'scope': 'exact root-supplied guarded runtime observation; no producer/method change'}
