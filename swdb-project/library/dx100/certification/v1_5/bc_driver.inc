
// ---- swdb certification driver, BC (certify 1.5; ticket 78, 2026-10-05 ET) ----
// Evaluator-owned; certify 1.4 keeps ../v1_4/bc_driver.inc. Appended to every build of the
// candidate; the candidate's own main is renamed (-Dmain=swdb_candidate_main) and never runs.
// The driver runs in the candidate process and writes no record: it calls the protected entry
// point Brandes once for the source and hands the location of the returned scores to the
// evaluator (swdb_client_finish, client.cc), which reads them from the shared arena itself.
#undef main
#undef Brandes
#undef Graph
#undef CLIterApp
#undef Builder
#undef NodeID
#undef ScoreT
#undef SourcePicker
#undef pvector
#undef ParseArgs
#undef MakeGraph
#undef start_vertex
#undef num_nodes
#undef data
#undef size
void swdb_client_finish(const void *base, size_t count, int kind);
static_assert(sizeof(ScoreT) == 4, "certification records 32-bit float scores");
int main(int argc, char *argv[]) {
  CLIterApp swdb_cert_cli(argc, argv, "swdb certification: betweenness centrality", 1);
  if (!swdb_cert_cli.ParseArgs()) return 2;
  Builder swdb_cert_builder(swdb_cert_cli);
  Graph swdb_cert_graph = swdb_cert_builder.MakeGraph();
  const int64_t swdb_cert_source = swdb_cert_cli.start_vertex();
  if (swdb_cert_source < 0 || swdb_cert_source >= int64_t(swdb_cert_graph.num_nodes())) return 3;
  SourcePicker<Graph> swdb_cert_picker(swdb_cert_graph, NodeID(swdb_cert_source));
  pvector<ScoreT> swdb_cert_scores = Brandes(swdb_cert_graph, swdb_cert_picker, 1);
  swdb_client_finish(swdb_cert_scores.data(), swdb_cert_scores.size(), 1);
  return 0;
}
