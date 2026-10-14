(* The proof hint check's syntax-tree reader: a Frama-C 33.0 module (loaded with -load-module).

   Created: 2026-10-14 ET (Probata proof of concept ticket 35). Design: formal-verification map 13 items 4, 5
   and 7 (the proof hint check reads Frama-C's syntax tree, not the text). Python side: swdb/hint_check.py.

   After Frama-C has parsed and type-checked a merged unit, this prints one JSON object per line for every
   annotation-like node of the syntax tree, with its file and line span: global logic declarations, lemmas,
   axiomatic blocks, modules (imports), invariants, volatile clauses, ACSL extensions, code annotations,
   function and statement contracts, ghost variables, ghost functions and ghost statements. It judges
   nothing: swdb/hint_check.py attributes each node to the hint whose lines hold it and applies the rules. *)

open Frama_c_kernel
open Cil_types

let out = Buffer.create 4096

let esc s =
  let b = Buffer.create (String.length s + 2) in
  String.iter
    (fun c ->
       match c with
       | '"' -> Buffer.add_string b "\\\""
       | '\\' -> Buffer.add_string b "\\\\"
       | '\n' -> Buffer.add_string b "\\n"
       | c when Char.code c < 32 -> Buffer.add_string b (Printf.sprintf "\\u%04x" (Char.code c))
       | c -> Buffer.add_char b c)
    s;
  "\"" ^ Buffer.contents b ^ "\""

let span (loc : location) =
  let (a, b) = loc in
  Printf.sprintf "\"file\": %s, \"line\": %d, \"end\": %d"
    (esc (Filepath.basename (Filepos.path a))) (Filepos.line a) (Filepos.line b)

let emit node loc fields =
  let extra = String.concat "" (List.map (fun (k, v) -> Printf.sprintf ", %s: %s" (esc k) v) fields) in
  Buffer.add_string out (Printf.sprintf "{\"node\": %s, %s%s}\n" (esc node) (span loc) extra)

let str s = esc s
let bool b = if b then "true" else "false"
let int n = string_of_int n
let strs l = "[" ^ String.concat ", " (List.map esc l) ^ "]"

let kind = function Assert -> "assert" | Check -> "check" | Admit -> "admit"

(* Names of logic functions and predicates used, string constants, unbounded ranges: one walk. *)
class collect = object
  inherit Visitor.frama_c_inplace
  val mutable used = []
  val mutable strings = []
  val mutable unbounded = false
  method used = used
  method strings = strings
  method unbounded = unbounded
  method! vlogic_info_use li = used <- li.l_var_info.lv_name :: used; Cil.DoChildren
  method! vterm_node = function
    | TConst (LStr s) -> strings <- s :: strings; Cil.DoChildren
    | Trange (lo, hi) -> if lo = None || hi = None then unbounded <- true; Cil.DoChildren
    | _ -> Cil.DoChildren
end

let walk_term c t = ignore (Visitor.visitFramacTerm (c :> Visitor.frama_c_visitor) t)
let walk_pred c p = ignore (Visitor.visitFramacPredicate (c :> Visitor.frama_c_visitor) p)

let body_kind = function
  | LBnone -> "none" | LBreads _ -> "reads" | LBterm _ -> "term" | LBpred _ -> "predicate"
  | LBinductive _ -> "inductive"

let recursive li =
  let c = new collect in
  (match li.l_body with
   | LBterm t -> walk_term c t
   | LBpred p -> walk_pred c p
   | LBinductive cases -> List.iter (fun (_, _, _, p) -> walk_pred c p) cases
   | LBreads l -> List.iter (fun it -> walk_term c it.it_content) l
   | LBnone -> ());
  List.mem li.l_var_info.lv_name c#used

let extension_fields ext =
  let c = new collect in
  (match ext.ext_kind with
   | Ext_terms l -> List.iter (walk_term c) l
   | Ext_preds l -> List.iter (walk_pred c) l
   | Ext_id _ | Ext_annot _ -> ());
  let shape = match ext.ext_kind with
    | Ext_terms _ -> "terms" | Ext_preds _ -> "predicates" | Ext_id _ -> "id" | Ext_annot _ -> "annot" in
  [ "plugin", str ext.ext_plugin; "name", str ext.ext_name; "shape", str shape;
    "strings", strs (List.rev c#strings); "uses", strs (List.rev c#used) ]

let rec global_annotation ?(inside = "") ga =
  let within = [ "inside", str inside ] in
  match ga with
  | Dfun_or_pred (li, loc) ->
    emit "logic_definition" loc
      ([ "name", str li.l_var_info.lv_name; "predicate", bool (li.l_type = None);
         "body", str (body_kind li.l_body); "recursive", bool (recursive li) ] @ within)
  | Dlemma (name, _, _, tp, _, loc) ->
    emit "lemma" loc ([ "name", str name; "kind", str (kind tp.tp_kind) ] @ within)
  | Daxiomatic (name, gas, _, loc) ->
    emit "axiomatic" loc ([ "name", str name ] @ within);
    List.iter (global_annotation ~inside:"axiomatic") gas
  | Dmodule (name, gas, _, loader, loc) ->
    let loader = match loader with
      | Some l -> l.loader_plugin ^ "::" ^ l.loader_name | None -> "" in
    emit "module" loc ([ "name", str name; "loader", str loader ] @ within);
    List.iter (global_annotation ~inside:"module") gas
  | Dtype (ti, loc) -> emit "logic_type" loc ([ "name", str ti.lt_name ] @ within)
  | Dinvariant (li, loc) -> emit "global_invariant" loc ([ "name", str li.l_var_info.lv_name ] @ within)
  | Dtype_annot (li, loc) -> emit "type_invariant" loc ([ "name", str li.l_var_info.lv_name ] @ within)
  | Dmodel_annot (mi, loc) -> emit "model_field" loc ([ "name", str mi.mi_name ] @ within)
  | Dvolatile (_, _, _, _, loc) -> emit "volatile" loc within
  | Dextended (ext, _, loc) -> emit "extension" loc (extension_fields ext @ within)

let pred_loc (ip : identified_predicate) = ip.ip_content.tp_statement.pred_loc

let spec_clauses where fallback (spec : spec) =
  let clause name loc = emit "contract_clause" loc [ "clause", str name; "of", str where ] in
  let predicate name (ip : identified_predicate) =
    emit "contract_clause" (pred_loc ip)
      [ "clause", str name; "of", str where; "kind", str (kind ip.ip_content.tp_kind) ] in
  List.iter
    (fun b ->
       List.iter (predicate "requires") b.b_requires;
       List.iter (predicate "assumes") b.b_assumes;
       List.iter (fun (_, ip) -> predicate "ensures" ip) b.b_post_cond;
       (match b.b_assigns with
        | Writes l -> List.iter (fun (it, _) -> clause "assigns" it.it_content.term_loc) l
        | WritesAny -> ());
       (match b.b_allocation with
        | FreeAlloc (a, f) -> List.iter (fun it -> clause "allocation" it.it_content.term_loc) (a @ f)
        | FreeAllocAny -> ());
       List.iter (fun e -> clause ("extension:" ^ e.ext_name) e.ext_loc) b.b_extended;
       if b.b_name <> Cil.default_behavior_name then clause "behavior" fallback)
    spec.spec_behavior;
  (match spec.spec_variant with Some (t, _) -> clause "decreases" t.term_loc | None -> ());
  (match spec.spec_terminates with Some ip -> predicate "terminates" ip | None -> ());
  if spec.spec_complete_behaviors <> [] then clause "complete" fallback;
  if spec.spec_disjoint_behaviors <> [] then clause "disjoint" fallback

(* A code annotation's own location; Frama-C keeps none for some (loop assigns \nothing, statement contracts):
   those carry the statement's location and "at_statement": the reader attributes them to the hints right above. *)
let code_annotation stmt ca =
  let own = match ca.annot_content with
    | AAssigns (_, Writes ((it, _) :: _)) -> Some it.it_content.term_loc
    | AAssigns _ | AStmtSpec _ -> None
    | _ -> Cil_datatype.Code_annotation.loc ca in
  let loc, at_statement = match own with
    | Some l -> l, false | None -> Cil_datatype.Stmt.loc stmt, true in
  let emit node loc fields = emit node loc (fields @ [ "at_statement", bool at_statement ]) in
  let behaviors l = [ "behaviors", int (List.length l) ] in
  match ca.annot_content with
  | AAssert (b, tp) -> emit "assert" loc ([ "kind", str (kind tp.tp_kind) ] @ behaviors b)
  | AInvariant (b, is_loop, tp) ->
    emit (if is_loop then "loop_invariant" else "code_invariant") loc
      ([ "kind", str (kind tp.tp_kind) ] @ behaviors b)
  | AVariant (t, rel) ->
    emit "loop_variant" loc
      [ "relation", bool (rel <> None); "integer", bool (Logic_utils.is_integral_type t.term_type) ]
  | AAssigns (b, assigns) ->
    let c = new collect in
    let from = ref false and any = ref false in
    (match assigns with
     | WritesAny -> any := true
     | Writes l ->
       List.iter
         (fun (it, deps) ->
            walk_term c it.it_content;
            match deps with From _ -> from := true | FromAny -> ())
         l);
    emit "loop_assigns" loc
      ([ "from", bool !from; "everything", bool !any; "unbounded_range", bool c#unbounded ] @ behaviors b)
  | AAllocation (b, _) -> emit "loop_allocation" loc (behaviors b)
  | AStmtSpec (b, spec) ->
    emit "statement_contract" loc (behaviors b);
    spec_clauses "statement" loc spec
  | AExtended (b, is_loop, ext) ->
    emit "code_extension" loc (extension_fields ext @ behaviors b @ [ "loop", bool is_loop ])

class ghost_statements = object
  inherit Visitor.frama_c_inplace
  method! vstmt_aux s =
    if s.ghost then emit "ghost_statement" (Cil_datatype.Stmt.loc s) [];
    Cil.DoChildren
end

let global = function
  | GAnnot (ga, _) -> global_annotation ga
  | GVar (vi, _, loc) | GVarDecl (vi, loc) when vi.vghost ->
    emit "ghost_variable" loc [ "name", str vi.vname; "scope", str "global" ]
  | GFun (fd, loc) ->
    if fd.svar.vghost then emit "ghost_function" loc [ "name", str fd.svar.vname; "body", bool true ]
    else begin
      List.iter
        (fun vi -> if vi.vghost then emit "ghost_variable" vi.vdecl [ "name", str vi.vname; "scope", str "local" ])
        fd.slocals;
      ignore (Visitor.visitFramacFunction (new ghost_statements) fd)
    end
  | GFunDecl (_, vi, loc) when vi.vghost ->
    emit "ghost_function" loc [ "name", str vi.vname; "body", bool false ]
  | _ -> ()

let run () =
  let file = Ast.get () in
  List.iter global file.globals;
  Globals.Functions.iter
    (fun kf ->
       let spec = Annotations.funspec kf in
       spec_clauses (Kernel_function.get_name kf) (Kernel_function.get_location kf) spec);
  Annotations.iter_all_code_annot ~sorted:true (fun stmt _ ca -> code_annotation stmt ca);
  let path = Sys.getenv_opt "SWDB_HINT_TREE_OUT" in
  match path with
  | Some p ->
    let oc = open_out p in
    output_string oc (Buffer.contents out);
    output_string oc "{\"node\": \"end\", \"file\": \"\", \"line\": 0, \"end\": 0}\n";
    close_out oc
  | None -> print_string (Buffer.contents out)

let () = Boot.Main.extend run
