(* Fresh-run inventory of ALL generated WP obligations, including never-tried goals.
   Created: 2026-10-15 ET (Probata ticket36). No consolidated Valid status
   establishes a proof. Individual Wpo results and generated IDs are independent
   of WP's report JSON (which omits untried goals). Extern is read separately. *)
open Frama_c_kernel

let esc s =
  let b = Buffer.create 80 in
  String.iter (function
    | '"' -> Buffer.add_string b "\\\""
    | '\\' -> Buffer.add_string b "\\\\"
    | '\n' -> Buffer.add_string b "\\n"
    | '\r' -> Buffer.add_string b "\\r"
    | '\t' -> Buffer.add_string b "\\t"
    | c when Char.code c < 32 -> Buffer.add_string b (Printf.sprintf "\\u%04x" (Char.code c))
    | c -> Buffer.add_char b c) s;
  "\"" ^ Buffer.contents b ^ "\""

let function_of p = match Property.get_kf p with
  | None -> "null" | Some kf -> esc (Kernel_function.get_name kf)
let loc p =
  let a, _ = Property.location p in
  Filepath.to_string_abs (Filepos.path a), Filepos.line a
let verdict = function
  | Wp.VCS.NoResult -> "untried" | Unknown -> "unknown" | Timeout -> "timeout"
  | Stepout -> "stepout" | Computing _ -> "computing" | Valid -> "valid"
  | Invalid -> "invalid" | Failed -> "failed"
let bool b = if b then "true" else "false"

let run () = match Sys.getenv_opt "SWDB_PROOF_REPORT_OUT" with
  | None -> ()
  | Some path ->
    let goals = ref [] in
    Wp.Wpo.iter_on_goals (fun w ->
        let p = Wp.Wpo.get_property w in
        let _, line = loc p in
        let targets = List.map (fun p -> esc (Property.Names.get_prop_name_id p))
            (Wp.WpPropId.doomed_if_valid w.Wp.Wpo.po_pid) in
        let best = List.map (fun (_, (r : Wp.VCS.result)) -> verdict r.verdict) (Wp.Wpo.get_results w) in
        goals := Printf.sprintf
            "{\"goal\":%s,\"property\":%s,\"function\":%s,\"line\":%d,\"smoke\":%s,\"passed\":%s,\"targets\":[%s],\"results\":[%s]}"
            (esc (Wp.Wpo.get_gid w)) (esc (Property.Names.get_prop_name_id p))
            (function_of p) line (bool (Wp.Wpo.is_smoke_test w)) (bool (Wp.Wpo.is_passed w))
            (String.concat "," targets) (String.concat "," (List.map esc best)) :: !goals);
    let properties = ref [] in
    Property_status.iter (fun p ->
        let file, line = loc p in
        (* System declarations belong to the pinned Frama-C installation. Every
           other source in the include closure is inspected, not just wp_input.c. *)
        let system = String.starts_with ~prefix:(Filepath.to_string_abs (Kernel.Share.get_dir "libc")) file in
        if not system then (
          let extern = Property_status.Feedback.get p = Property_status.Feedback.Considered_valid in
          let emitter_name = match p with
            | Property.IPCodeAnnot ca -> Emitter.get_name (Annotations.emitter_of_code_annot ca.ica_ca ca.ica_stmt)
            | _ -> "" in
          let smoke_failure = match p with
            | Property.IPCodeAnnot ca ->
              let e = Annotations.emitter_of_code_annot ca.ica_ca ca.ica_stmt in
              let name = Emitter.get_name e in
              (match ca.ica_ca.annot_content with
               | Cil_types.AAssert (_, tp) ->
                 (String.starts_with ~prefix:"Wp" name || name = "Unreachable Annotations") && tp.tp_statement.pred_name = ["Wp"; "SmokeTest"]
               | _ -> false)
            | _ -> false in
          let dependencies = Property_status.fold_on_statuses
              (fun e _ acc -> List.fold_left (fun acc p -> Property.Names.get_prop_name_id p :: acc)
                  acc e.Property_status.properties) p [] in
          let dependencies = List.sort_uniq String.compare dependencies in
          let origin = match p with
            | Property.IPPropertyInstance instance -> esc (Property.Names.get_prop_name_id instance.ii_ip)
            | _ -> "null" in
          let kind = match p with
            | Property.IPPredicate _ -> "contract"
            | Property.IPAssigns _ | Property.IPAllocation _ | Property.IPFrom _ -> "contract"
            | Property.IPDecrease _ -> "termination"
            | Property.IPLemma _ -> "lemma"
            | _ -> "other" in
          properties := Printf.sprintf
              "{\"property\":%s,\"function\":%s,\"kind\":%s,\"emitter\":%s,\"origin\":%s,\"dependencies\":[%s],\"extern\":%s,\"generated_smoke_failure\":%s,\"line\":%d,\"description\":%s}"
              (esc (Property.Names.get_prop_name_id p)) (function_of p) (esc kind) (esc emitter_name) origin (String.concat "," (List.map esc dependencies)) (bool extern) (bool smoke_failure) line
              (esc (Format.asprintf "%a" Property.pretty p)) :: !properties));
    let oc = open_out path in
    Printf.fprintf oc "{\"version\":\"1\",\"goals\":[%s],\"properties\":[%s],\"complete\":true}\n"
      (String.concat "," (List.rev !goals)) (String.concat "," (List.rev !properties));
    close_out oc
let () = Boot.Main.extend run
