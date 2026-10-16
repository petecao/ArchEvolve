# Independent frame-test repair review

**PASS for the narrow test-only repair at `ece76ebc6e32c5f1d43ccdf2aa65d7913cf6dec7`.** Its entire diff from188 changes only `tests/test_dx100_initialized_register.py`; production and other tracked bytes are unchanged.

The helper requires one exact `trust_fixture.contract` anchor and the ACSL comment immediately before `int trust_fixture(void) {`. It requires a sole `assigns` clause and uses the ordinary public ACSL lexer to compare exactly the four expected locations, including the unchanged `[0..1]` extent. The lexer consumes all noncomment/nonwhitespace characters or refuses; this does not erase token boundaries. Other original public assertions remain. This is a closed generated-target assertion, not a generic ACSL parser or frame-soundness theorem.

The retained actual WP input2d77a84e…b158c reproduces the original assertion RED and satisfies the new helper. Seven retained mutations refuse widening, omitted/changed counters or cells, an extra location, duplicate assigns and a misleading correct helper frame beside a wrong target. Matched guard logs report RED exit1/0.374606s/18.015625MiB and GREEN exit0/0.369650s/21.484375MiB, no timeout/OOM inspection events/failure/children. These are author-retained pure controls; this reviewer did not rerun them.

V1 remains failed and unchanged. A fresh public workflow, compiler/native/formal result, model/body, hardware/current0.2 or ticket acceptance is not claimed. The eventual merged source/policy/packet still requires root’s independent fresh admission. No source mutation, project import, entry/main, control/test rerun, compiler/native/formal, B or SSH execution occurred in this review.
