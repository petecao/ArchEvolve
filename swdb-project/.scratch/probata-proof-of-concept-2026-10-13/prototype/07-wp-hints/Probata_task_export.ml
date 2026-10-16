(* Read-only machine task exporter component, 2026-10-15 ET. No verdict. *)
let export () =
  let tasks = ref [] in
  let seen = Hashtbl.create 97 in
  Wp.Wpo.iter_on_goals (fun goal ->
    let id = Wp.Wpo.get_gid goal in
    if Hashtbl.mem seen id then failwith ("duplicate WP machine goal ID: " ^ id);
    Hashtbl.add seen id ();
    let task = Format.asprintf "%a" Wp.Wpo.pp_goal goal in
    tasks := (id, `String task) :: !tasks);
  let payload = `Assoc ["schema", `String "probata-wpo-tasks-v1";
                        "tasks", `Assoc (List.sort compare !tasks)] in
  let channel = open_out "wp-task-index.json" in
  Fun.protect ~finally:(fun () -> close_out channel)
    (fun () -> Yojson.Basic.to_channel channel payload)
let () = Frama_c_kernel.Boot.Main.extend export
