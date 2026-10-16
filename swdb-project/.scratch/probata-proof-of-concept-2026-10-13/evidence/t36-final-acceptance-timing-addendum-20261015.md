# Ticket 36 acceptance timing addendum

Updated: 2026-10-15 ET. **PASS; final acceptance disposition unchanged.** This adds an exact-byte packet update to the preserved final receipt `probata-t36-final-acceptance-independent-review-final-20261015.md` (SHA-256 `844af84b64d1c1cbf36ef7707648e20f79b356b2a1431fc6cda83035f23252ab`). No tests, compiler, verifier, remote commands, or repository mutations were performed by the reviewer.

Current `evidence/t36-setup-bounded-cold-20261015.json` SHA-256 is `80860adde1c9ecb812de55f5b3198047d256d813300654fdac0ea7a8a45f7fcf`. Removing only its new top-level `lease_closure` field and serializing with the existing indentation/newline exactly reproduces the previously reviewed packet hash `5223be18527b1de034e6fb05d95df4a66322368093af2cfc3dddb86c62715e0e`. All previous acceptance evidence bytes represented in that packet are unchanged.

The added field attributes direct lease verification to root: setup node0 generation583 released2026-10-15 22:21:17ET; bounded node1 generation609 released22:16:09ET. Both were observed released at22:22:37ET, and root's subsequent direct verification was at22:24:36ET. Release times and observation times are explicitly distinguished. I reviewed the matching explanatory issue36 Answer lines; their scope and timing distinction are accurate. This is review of root-supplied metadata, not a new independent remote lease check.

No source, test, method/checker identity, scope, result or ten-item acceptance disposition changes. The exact2033/74+b493 boundaries and original production pytest failure/cold assertion correction remain as accepted in the preserved final receipt.
