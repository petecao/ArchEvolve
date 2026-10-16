# Smoke observations in the public WP reader

2026-10-16 ET. Reader repair only. The preserved 47b310df property-closure
checkpoint and its receipts remain separate. No new formal run, proof-record
promotion, source refinement, initialization/lifetime, TD, or provider-count
acceptance follows from these data-fixture controls.

A smoke goal with passed=true and results=[] previously allowed a proof record
to be accepted. Installed Wpo.ml lines 753–761 defines all_not_valid with
List.for_all: the empty list therefore passes vacuously. Failed and untried
results also cannot establish an attempted healthy smoke check. The public
read_wp_reports interface now requires a nonempty list containing only unknown,
timeout, stepout, or invalid for any smoke goal whose pass flag is true. The
inventory pass flag must be Boolean. A false flag still refuses acceptance,
even if nonvalid results exist, because trivial contradictory smoke can have
passed=false independently of the result list.

When native JSON contains that goal, its property identity, smoke/pass flags,
and best verdict must agree with the inventory. Its verdict must be one of the
healthy observed inventory states. A missing native row can still be read from
the mandatory complete inventory. Native caller and property callee function
names are deliberately not equated: installed register.ml serializes function
from po_idx, while the inventory associates the property with its callee for
call-smoke goals. Exact source-context reconciliation remains an independent
actual-packet gate.

Unknown, timeout, stepout, and invalid are retained operational observations.
This reader policy supplies no satisfiability or assumption-consistency theorem.
An inventory containing any valid, failed, untried, computing, unexpected,
malformed, or absent result refuses acceptance. Native disagreement likewise
refuses acceptance. Ordinary proof, complete property-reference closure, pinned
Extern, and failed-smoke behavior retain their existing gates. The changed
consumer participates in the existing source-bundle checker identity.

The authorized public test seam is read_wp_reports, plus affected labeled
synthetic CLI/persistence controls. Genuine RED receipts retain 19 false
acceptances among 27 smoke cases and a separate two-case malformed pass-flag
bypass. Synthetic healthy fixtures were corrected to unknown smoke observations
rather than valid contradictions or empty results. These fixtures are not actual
solver evidence. The final preparation JSON pins the exact control logs and
source bytes, including an overbroad 90-second profile that timed out and is not
claimed passed. The final profile selects affected cases explicitly.

The production OCaml reporter is unchanged from 47b310df/2fa269a9. Root's separate
native compilation succeeded in probata-t07-native-report-compile-v2-20261016;
this establishes API compilation only. The original positive export still has
43 missing property rows and remains refused. The next actual export component
may cover only the two previously unexecuted cases after independent source and
packet review and root admission. The complete generated-goal census, native
report closure, backend task/Init bindings, resource/lease settlement, and all
source/lifetime boundaries remain required.
