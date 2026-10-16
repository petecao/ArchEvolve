(* Read-only WP source/backend binding observer with flushed first snapshots,
   2026-10-16 ET. Separate successor; original observer and actuals are preserved.
   No goal reduction, proof, status update, assumption, or memory fact is added.
   First-add snapshots are only as early/unreduced as the installed hook permits.
   The stream makes no early Property.Names query. The existing journal's literal
   property name joins by GID only within the same invocation, never as an alias. *)
open Frama_c_kernel

let esc s =
  let b = Buffer.create 80 in
  String.iter (function
    | '"' -> Buffer.add_string b "\\\""
    | '\\' -> Buffer.add_string b "\\\\"
    | '\n' -> Buffer.add_string b "\\n"
    | '\r' -> Buffer.add_string b "\\r"
    | '\t' -> Buffer.add_string b "\\t"
    | c when Char.code c < 32 ->
      Buffer.add_string b (Printf.sprintf "\\u%04x" (Char.code c))
    | c -> Buffer.add_char b c) s;
  "\"" ^ Buffer.contents b ^ "\""

let bool b = if b then "true" else "false"
let verdict = function
  | Wp.VCS.NoResult -> "untried" | Unknown -> "unknown" | Timeout -> "timeout"
  | Stepout -> "stepout" | Computing _ -> "computing" | Valid -> "valid"
  | Invalid -> "invalid" | Failed -> "failed"

let result_rows w =
  List.map (fun (p, (r : Wp.VCS.result)) ->
      Printf.sprintf "{\"prover\":%s,\"external\":%s,\"verdict\":%s}"
        (esc (Wp.Prover.ident p)) (bool (Wp.Prover.is_extern p))
        (esc (verdict r.verdict))) (Wp.Wpo.get_results w)

let snapshot w =
  let annotation = w.Wp.Wpo.po_formula in
  let goal = annotation.Wp.Wpo.VC_Annot.goal in
  let computed = Wp.Wpo.GOAL.is_computed goal in
  let trivial = Wp.Wpo.is_trivial w in
  let results = result_rows w in
  (* get_descr returns the current sequent without compute/resolve/reduce.
     Pcond.pretty formats that sequent; unlike Wpo.pp_goal it does not call
     GOAL.compute_descr. The observer never requests simplification. *)
  let sequent = Wp.Wpo.GOAL.get_descr goal in
  let text = Wp.WpContext.on_context (Wp.Wpo.get_context w)
      (fun () -> Format.asprintf "%a" Wp.Pcond.pretty sequent) () in
  if computed <> Wp.Wpo.GOAL.is_computed goal ||
     trivial <> Wp.Wpo.is_trivial w || results <> result_rows w then
    failwith "binding observer changed goal computation or result state";
  Printf.sprintf
    "{\"computed\":%s,\"trivial\":%s,\"results\":[%s],\"sequent\":%s}"
    (bool computed) (bool trivial) (String.concat "," results) (esc text)

let first : (string, string) Hashtbl.t = Hashtbl.create 401
let enabled () = Sys.getenv_opt "SWDB_WP_BINDINGS_OUT" <> None
let append_stream event =
  match Sys.getenv_opt "SWDB_WP_BINDINGS_STREAM_OUT" with
  | None -> ()
  | Some path ->
    let phase = match Sys.getenv_opt "SWDB_WP_COMPONENT_PHASE" with
      | Some (("generation" | "proof") as phase) -> phase
      | _ -> failwith "binding stream requires explicit generation/proof phase"
    in
    let oc = open_out_gen [Open_wronly;Open_creat;Open_append;Open_text] 0o600 path in
    output_string oc ("{\"phase\":" ^ esc phase ^ "," ^ event ^ "}\n");
    flush oc; close_out oc
let stream_first w id initial =
  let p = Wp.Wpo.get_property w in
  let a, _ = Property.location p in
  let fn = match Property.get_kf p with
    | None -> "null" | Some kf -> esc (Kernel_function.get_name kf) in
  append_stream (Printf.sprintf
      "\"event\":\"first\",\"goal\":%s,\"short_id\":%s,\"backend_property_id\":%s,\"function\":%s,\"source_file\":%s,\"line\":%d,\"smoke\":%s,\"first_observed\":%s"
      (esc id) (esc w.Wp.Wpo.po_sid)
      (esc (Wp.WpPropId.get_propid w.Wp.Wpo.po_pid)) fn
      (esc (Filepath.to_string_abs (Filepos.path a))) (Filepos.line a)
      (bool (Wp.Wpo.is_smoke_test w)) initial)
let observe w =
  if enabled () then begin
    let id = Wp.Wpo.get_gid w in
    if not (Hashtbl.mem first id) then begin
      let initial = snapshot w in
      Hashtbl.add first id initial;
      stream_first w id initial
    end
  end

let run () = match Sys.getenv_opt "SWDB_WP_BINDINGS_OUT" with
  | None -> ()
  | Some path ->
    let rows = ref [] in
    Wp.Wpo.iter_on_goals (fun w ->
        let p = Wp.Wpo.get_property w in
        let a, _ = Property.location p in
        let fn = match Property.get_kf p with
          | None -> "null" | Some kf -> esc (Kernel_function.get_name kf) in
        let id = Wp.Wpo.get_gid w in
        let initial = match Hashtbl.find_opt first id with
          | None -> "null" | Some s -> s in
        rows := Printf.sprintf
          "{\"goal\":%s,\"short_id\":%s,\"backend_property_id\":%s,\"property\":%s,\"function\":%s,\"source_file\":%s,\"line\":%d,\"smoke\":%s,\"first_observed\":%s,\"final_observed\":%s}"
          (esc id) (esc w.Wp.Wpo.po_sid)
          (esc (Wp.WpPropId.get_propid w.Wp.Wpo.po_pid))
          (esc (Property.Names.get_prop_name_id p)) fn
          (esc (Filepath.to_string_abs (Filepos.path a))) (Filepos.line a)
          (bool (Wp.Wpo.is_smoke_test w)) initial (snapshot w) :: !rows);
    let oc = open_out path in
    Printf.fprintf oc
      "{\"version\":\"1\",\"complete\":true,\"read_only\":true,\"proof_acceptance\":false,\"goals\":[%s]}\n"
      (String.concat "," (List.rev !rows));
    close_out oc

let () =
  Wp.Wpo.add_modified_hook observe;
  Wp.Wpo.add_cleared_hook (fun () ->
      Hashtbl.clear first;
      append_stream "\"event\":\"cleared\"");
  Boot.Main.extend run
