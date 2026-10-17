"""Shared test support. Created 2026-10-05 ET (code review T1-T3).

Modules here hold fixtures and helpers that several test modules use. Fixture modules are
registered by `tests/conftest.py` (`pytest_plugins`); helpers are imported explicitly. No test
module imports another test module, and no fixture is called through `__wrapped__`: module-scoped
seeds use the plain builders (`conftest.make_records`, `proposals.build_proposal_setup`, ...).
"""
