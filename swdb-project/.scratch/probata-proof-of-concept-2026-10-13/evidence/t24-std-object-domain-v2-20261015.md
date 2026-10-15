# Ticket24 std contract qualification v2, 2026-10-15 ET

The first qualified profile at exact source6221 stopped at **public validation**, before creating any new proof record or launching WP. Its eight errors reject `\valid_read` and `\base_addr` in formal halves. The 11 earlier compiler/parser controls checked Frama-C typechecking but missed the public ACSL vocabulary boundary. The immutable failed launch and independent bootstrap audit remain preserved in `t24-qualified-bootstrap-independent-review-20261015.{md,json}`. No actual dependency selection or qualified proof is claimed for that run.

The new separately named contract is `contract.fixture_wp24_std_models_object_domain_v2`, canonical SHA-256 `d586c9414b4ea374e9a0173f7b66b0de6ba0d19e3637f2da8d0bcc139baa61fe`. It retains the exact original source, function, array domains and all original clauses. The added n=0 qualification is now explicitly stronger and uses the existing allowed vocabulary:

```acsl
requires n == 0 ==> (
  (a == \null || \valid(a) || \valid(a - 1)) &&
  (b == \null || \valid(b) || \valid(b - 1)));
```

This proposes a writable-object or writable-predecessor domain for empty inputs. Null, writable live bases, writable live one-past inputs and original positive-length inputs remain intended witnesses. Read-only empty objects and live zero-size allocations remain outside this conservative fixture qualification; neither is classified UB. No new read-only native outcome is claimed. The existing native zero-size success remains a diagnostic, not a portable proof or a v2 domain certificate.

The generated same-base/object-or-one-past assertion remains unchanged. The validity of a predecessor is intended to discharge that assertion under the typed memory model; **actual WP must still prove it**, along with every original numerical, RTE, initialization, range, frame, postcondition and smoke goal. Public validation and typechecking do not waive that obligation. No production vocabulary expansion, model change or hidden adapter premise is introduced.

The original actual std contract remains `13fd0509e48eb0d9f45e8e6edc9a0fd5a4fec66d45f3e3cc525ee072b09c57d9` and not proven on `swdb_pointer_formation_1`. The rejected readable-qualified contract remains independently reproducible as `rejected_readable_contract`, original ID and canonical pin `762deba8e2d8dc8961500d26209a6857553993225eadb0da6a12a8ba3b0c341a`. Its exact eight public validation errors are a permanent negative control. These are three distinct states: original actual failure, first qualification admission failure, and v2 actual acceptance pending.

The new public-validation test first failed with those same eight errors (real RED). After the test/contract-only change, the entire 13-control profile passes: public v2 validation, preserved v1 refusal, original source/clause preservation and mutation controls, real Frama typecheck/wrong-field negative, timeout and read-only output guards. A final focused three-control run preserves both public command outputs plus Frama typechecking. No actual verifier ran locally. Resource and physical artifact pins appear in the accompanying JSON. The new `wp-std-domain-public-vocabulary` corpus entry links the admission failure and replay; the original empty-domain corpus now names v2 explicitly.

The reviewed runner preserves its output disjointness, exact source/runtime/method/model qualification checks and ordinary public dependency eligibility. It writes the new contract to a distinct v2 file and labels actual rows `std_models_object_domain_v2:safe` and `:seeded`. It still copies the five ordinarily eligible original0e7 model records into a fresh workspace; their IDs are verified against the public resolver's actual selected pins after each proof. The original failed contract and input seed remain intact. Production `swdb/` bytes remain exactly0e7.

Assumption for the next actual profile: the five source0e7 model records remain ordinarily eligible in the exact launch tool environment. Eligibility failure must remain a refusal. The root coordinator owns the fresh reviewed-source launch and socket lease; no solver rerun or remote source change was performed for this correction. Actual qualified safe/seeded acceptance remains pending.
