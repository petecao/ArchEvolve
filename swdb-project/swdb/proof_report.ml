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

let is_system p =
  let file, _ = loc p in
  String.starts_with
    ~prefix:(Filepath.to_string_abs (Kernel.Share.get_dir "libc")) file

let dependencies p =
  Property_status.fold_on_statuses
    (fun e _ acc -> List.rev_append e.Property_status.properties acc) p []

let run () = match Sys.getenv_opt "SWDB_PROOF_REPORT_OUT" with
  | None -> ()
  | Some path ->
    (* Status iteration alone is not a property census. -wp-status-all can
       bypass the lookup which lazily registers synthetic smoke IPOther values.
       Snapshot registered objects; union actual Wpo references without asking
       the status API to register those missing properties. 2026-10-16 ET. *)
    let registered = ref Property.Set.empty in
    let registered_order = ref [] in
    Property_status.iter (fun p ->
        registered := Property.Set.add p !registered;
        registered_order := p :: !registered_order);
    let references = ref [] in
    let smoke_properties = ref Property.Set.empty in
    let goals = ref [] in
    Wp.Wpo.iter_on_goals (fun w ->
        let p = Wp.Wpo.get_property w in
        references := p :: !references;
        if Wp.Wpo.is_smoke_test w then
          smoke_properties := Property.Set.add p !smoke_properties;
        let _, line = loc p in
        let doomed = Wp.WpPropId.doomed_if_valid w.Wp.Wpo.po_pid in
        references := List.rev_append doomed !references;
        let targets = List.map (fun p -> esc (Property.Names.get_prop_name_id p))
            doomed in
        let best = List.map (fun (_, (r : Wp.VCS.result)) -> verdict r.verdict) (Wp.Wpo.get_results w) in
        goals := Printf.sprintf
            "{\"goal\":%s,\"property\":%s,\"function\":%s,\"line\":%d,\"smoke\":%s,\"passed\":%s,\"targets\":[%s],\"results\":[%s]}"
            (esc (Wp.Wpo.get_gid w)) (esc (Property.Names.get_prop_name_id p))
            (function_of p) line (bool (Wp.Wpo.is_smoke_test w)) (bool (Wp.Wpo.is_passed w))
            (String.concat "," targets) (String.concat "," (List.map esc best)) :: !goals);
    let exported = ref Property.Set.empty in
    let pending = Queue.create () in
    let order = ref [] in
    let include_property p =
      if not (Property.Set.mem p !exported) then begin
        exported := Property.Set.add p !exported;
        Queue.add p pending;
        order := p :: !order
      end in
    List.iter (fun p -> if not (is_system p) then include_property p)
      (List.rev !registered_order);
    List.iter include_property (List.rev !references);
    while not (Queue.is_empty pending) do
      let p = Queue.take pending in
      List.iter include_property (dependencies p);
      match p with
      | Property.IPPropertyInstance instance -> include_property instance.ii_ip
      | _ -> ()
    done;
    let unregistered_smokes = ref [] in
    let names = Hashtbl.create 401 in
    let properties = ref [] in
    List.iter (fun p ->
          let _, line = loc p in
          let name = Property.Names.get_prop_name_id p in
          if Hashtbl.mem names name then failwith "duplicate exported property identity";
          Hashtbl.add names name ();
          let is_registered = Property.Set.mem p !registered in
          let extern =
            if is_registered then
              Property_status.Feedback.get p = Property_status.Feedback.Considered_valid
            else match p with
              | Property.IPOther other
                when Property.Set.mem p !smoke_properties &&
                     String.starts_with ~prefix:"wp_smoke_" other.io_name ->
                (* A live WP smoke reference, no registered/emitted status.
                   Do not call Feedback.get: its lazy status lookup would
                   register this IPOther. No assumption is introduced. *)
                if dependencies p <> [] then
                  failwith "unregistered smoke unexpectedly has status dependencies";
                unregistered_smokes := esc name :: !unregistered_smokes;
                false
              | _ -> failwith "unclassified unregistered property reference" in
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
          let dependencies = List.map Property.Names.get_prop_name_id (dependencies p) in
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
              "{\"property\":%s,\"function\":%s,\"kind\":%s,\"emitter\":%s,\"origin\":%s,\"dependencies\":[%s],\"extern\":%s,\"generated_smoke_failure\":%s,\"line\":%d,\"description\":%s,\"status_registered\":%s,\"property_export_origin\":%s}"
              (esc name) (function_of p) (esc kind) (esc emitter_name) origin (String.concat "," (List.map esc dependencies)) (bool extern) (bool smoke_failure) line
              (esc (Format.asprintf "%a" Property.pretty p)) (bool is_registered)
              (esc (if is_registered then "registered" else "wp-smoke-reference")) :: !properties)
      (List.rev !order);
    let oc = open_out path in
    Printf.fprintf oc "{\"version\":\"1\",\"goals\":[%s],\"properties\":[%s],\"complete\":true,\"property_closure\":{\"registered_snapshot_count\":%d,\"exported_count\":%d,\"unregistered_wp_smoke_properties\":[%s],\"unregistered_status_lookup_performed\":false}}\n"
      (String.concat "," (List.rev !goals)) (String.concat "," (List.rev !properties))
      (Property.Set.cardinal !registered) (Property.Set.cardinal !exported)
      (String.concat "," (List.rev !unregistered_smokes));
    close_out oc
let () = Boot.Main.extend run
