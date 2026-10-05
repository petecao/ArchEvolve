
// ---- swdb certification driver, BFS (certify 1.4; ticket 76, 2026-10-05 ET) ----
// Evaluator-owned; certify 1.3 keeps ../bfs_driver.inc. Appended to every build of the candidate;
// the candidate's own main is renamed (-Dmain=swdb_candidate_main) and never runs. The driver
// records the source vertex, calls the protected entry point DOBFS once, and records the vector
// it returns and that vector's buffer (the array the candidate's claims must address, ticket 76).
// Names it uses are first freed of any candidate macro.
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
void swdb_cert_record_source(int64_t source);
void swdb_cert_record_result_i32(const int32_t *values, size_t count);
void swdb_cert_record_result_base(const void *base, size_t count);
void swdb_cert_record_end();
static_assert(sizeof(NodeID) == 4, "certification records 32-bit parent IDs");
int main(int argc, char *argv[]) {
  CLApp swdb_cert_cli(argc, argv, "swdb certification: breadth-first search");
  if (!swdb_cert_cli.ParseArgs()) return 2;
  Builder swdb_cert_builder(swdb_cert_cli);
  Graph swdb_cert_graph = swdb_cert_builder.MakeGraph();
  const int64_t swdb_cert_source = swdb_cert_cli.start_vertex();
  if (swdb_cert_source < 0 || swdb_cert_source >= int64_t(swdb_cert_graph.num_nodes())) return 3;
  swdb_cert_record_source(swdb_cert_source);
  pvector<NodeID> swdb_cert_parent = DOBFS(swdb_cert_graph, NodeID(swdb_cert_source));
  swdb_cert_record_result_i32(reinterpret_cast<const int32_t *>(swdb_cert_parent.data()), swdb_cert_parent.size());
  swdb_cert_record_result_base(swdb_cert_parent.data(), swdb_cert_parent.size());
  swdb_cert_record_end();
  return 0;
}
