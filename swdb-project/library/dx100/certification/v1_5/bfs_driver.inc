
// ---- swdb certification driver, BFS (certify 1.5; ticket 78, 2026-10-05 ET) ----
// Evaluator-owned; certify 1.4 keeps ../v1_4/bfs_driver.inc. Appended to every build of the
// candidate; the candidate's own main is renamed (-Dmain=swdb_candidate_main) and never runs.
// The driver runs in the candidate process and writes no record: it calls the protected entry
// point DOBFS once and hands the location of the returned vector to the evaluator
// (swdb_client_finish, client.cc). The evaluator records the source from its own arguments and
// reads the returned vector and its buffer address from the shared arena itself.
#undef main
#undef DOBFS
#undef Graph
#undef CLApp
#undef Builder
#undef NodeID
#undef pvector
#undef ParseArgs
#undef MakeGraph
#undef start_vertex
#undef num_nodes
#undef data
#undef size
void swdb_client_finish(const void *base, size_t count, int kind);
static_assert(sizeof(NodeID) == 4, "certification records 32-bit parent IDs");
int main(int argc, char *argv[]) {
  CLApp swdb_cert_cli(argc, argv, "swdb certification: breadth-first search");
  if (!swdb_cert_cli.ParseArgs()) return 2;
  Builder swdb_cert_builder(swdb_cert_cli);
  Graph swdb_cert_graph = swdb_cert_builder.MakeGraph();
  const int64_t swdb_cert_source = swdb_cert_cli.start_vertex();
  if (swdb_cert_source < 0 || swdb_cert_source >= int64_t(swdb_cert_graph.num_nodes())) return 3;
  pvector<NodeID> swdb_cert_parent = DOBFS(swdb_cert_graph, NodeID(swdb_cert_source));
  swdb_client_finish(swdb_cert_parent.data(), swdb_cert_parent.size(), 0);
  return 0;
}
