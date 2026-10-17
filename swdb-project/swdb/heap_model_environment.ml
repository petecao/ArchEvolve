(* Metadata only: no theory parsing, VC generation or prover invocation.
   Created 2026-10-15 ET, ticket25. Linked against the selected WP/Why3 runtime. *)
let () =
  let config = Why3.Whyconf.read_config None in
  let main = Why3.Whyconf.get_main config in
  List.iter
    (fun path -> output_string stdout path; output_char stdout '\000')
    (Why3.Whyconf.loadpath main)
