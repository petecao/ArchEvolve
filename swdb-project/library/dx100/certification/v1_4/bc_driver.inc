
// ---- swdb certification driver, BC (certify 1.4; ticket 76, 2026-10-05 ET) ----
// Evaluator-owned; certify 1.3 keeps ../bc_driver.inc. Appended to every build of the candidate;
// the candidate's own main is renamed (-Dmain=swdb_candidate_main) and never runs. The driver
// records the source vertex, calls the protected entry point Brandes once for that source, and
// records the scores it returns. Names it uses are first freed of any candidate macro.
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
void swdb_cert_record_source(int64_t source);
void swdb_cert_record_result_f32(const float *values, size_t count);
void swdb_cert_record_end();
static_assert(sizeof(ScoreT) == 4, "certification records 32-bit float scores");
int main(int argc, char *argv[]) {
  CLIterApp swdb_cert_cli(argc, argv, "swdb certification: betweenness centrality", 1);
  if (!swdb_cert_cli.ParseArgs()) return 2;
  Builder swdb_cert_builder(swdb_cert_cli);
  Graph swdb_cert_graph = swdb_cert_builder.MakeGraph();
  const int64_t swdb_cert_source = swdb_cert_cli.start_vertex();
  if (swdb_cert_source < 0 || swdb_cert_source >= int64_t(swdb_cert_graph.num_nodes())) return 3;
  swdb_cert_record_source(swdb_cert_source);
  SourcePicker<Graph> swdb_cert_picker(swdb_cert_graph, NodeID(swdb_cert_source));
  pvector<ScoreT> swdb_cert_scores = Brandes(swdb_cert_graph, swdb_cert_picker, 1);
  swdb_cert_record_result_f32(reinterpret_cast<const float *>(swdb_cert_scores.data()), swdb_cert_scores.size());
  swdb_cert_record_end();
  return 0;
}
