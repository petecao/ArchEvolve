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
        let best = List.map (fun (_, (r : Wp.VCS.result)) -> verdict r.verdict) (Wp.Wpo.get_results w) in
        goals := Printf.sprintf
            "{\"goal\":%s,\"property\":%s,\"function\":%s,\"line\":%d,\"smoke\":%s,\"passed\":%s,\"results\":[%s]}"
            (esc (Wp.Wpo.get_gid w)) (esc (Property.Names.get_prop_name_id p))
            (function_of p) line (bool (Wp.Wpo.is_smoke_test w)) (bool (Wp.Wpo.is_passed w))
            (String.concat "," (List.map esc best)) :: !goals);
    let properties = ref [] in
    Property_status.iter (fun p ->
        let file, line = loc p in
        (* System declarations belong to the pinned Frama-C installation. Every
           other source in the include closure is inspected, not just wp_input.c. *)
        let system = String.starts_with ~prefix:(Filepath.to_string_abs (Kernel.Share.get_dir "libc")) file in
        if not system then (
          let extern = Property_status.Feedback.get p = Property_status.Feedback.Considered_valid in
          let kind = match p with
            | Property.IPPredicate _ -> "contract"
            | Property.IPAssigns _ | Property.IPAllocation _ | Property.IPFrom _ -> "contract"
            | Property.IPDecrease _ -> "termination"
            | Property.IPLemma _ -> "lemma"
            | _ -> "other" in
          properties := Printf.sprintf
              "{\"property\":%s,\"function\":%s,\"kind\":%s,\"extern\":%s,\"line\":%d,\"description\":%s}"
              (esc (Property.Names.get_prop_name_id p)) (function_of p) (esc kind) (bool extern) line
              (esc (Format.asprintf "%a" Property.pretty p)) :: !properties));
    let oc = open_out path in
    Printf.fprintf oc "{\"version\":\"1\",\"goals\":[%s],\"properties\":[%s],\"complete\":true}\n"
      (String.concat "," (List.rev !goals)) (String.concat "," (List.rev !properties));
    close_out oc
let () = Boot.Main.extend run
